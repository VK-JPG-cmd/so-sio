from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import __version__
from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.exceptions import setup_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.db.session import close_db_engine

settings = get_settings()
logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan managing startup and graceful shutdown."""
    setup_logging(log_level=settings.LOG_LEVEL, environment=settings.ENVIRONMENT)
    logger.info(
        f"Starting {settings.APP_NAME} v{__version__} [Environment: {settings.ENVIRONMENT}]"
    )
    logger.info(f"API v1 prefix mounted at: {settings.API_V1_PREFIX}")

    # Auto-initialize database tables if needed
    try:
        from app.db.base import Base
        from app.db.session import engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified/created successfully.")
    except Exception as e:
        logger.warning(f"Database schema auto-init warning: {e}")

    # Launch background continuous threat discovery worker if configured
    if settings.THREAT_DISCOVERY_WORKER_ENABLED:
        from app.services.discovery.worker import discovery_worker
        discovery_worker.start()

    yield

    logger.info(f"Shutting down {settings.APP_NAME}...")
    if settings.THREAT_DISCOVERY_WORKER_ENABLED:
        from app.services.discovery.worker import discovery_worker
        await discovery_worker.stop()

    await close_db_engine()
    logger.info("Database connection pools disposed.")


def create_application() -> FastAPI:
    """Application factory for BrandShield AI FastAPI backend."""
    is_production = settings.ENVIRONMENT.lower() == "production"

    app = FastAPI(
        title=settings.APP_NAME,
        version=__version__,
        description=(
            "BrandShield AI — AI-powered Digital Risk Protection platform "
            "designed to identify impersonation, fake profiles, scam content, "
            "suspicious domains, and malicious applications."
        ),
        docs_url=None if is_production else "/docs",
        redoc_url=None if is_production else "/redoc",
        openapi_url=None if is_production else "/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS middleware
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.BACKEND_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=[
                "Authorization",
                "Content-Type",
                "Accept",
                "Origin",
                "X-Requested-With",
                "X-Total-Count",
                "X-Page",
                "X-Page-Size",
            ],
            expose_headers=["X-Total-Count", "X-Page", "X-Page-Size"],
        )

    # Register centralized exception handlers
    setup_exception_handlers(app)

    # Security headers middleware
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    # Mount API v1 router
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    # Mount interactive command center dashboard
    from app.api.dashboard import router as dashboard_router
    app.include_router(dashboard_router)

    return app


app = create_application()
