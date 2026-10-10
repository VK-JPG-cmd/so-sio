from datetime import datetime, timezone
from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse
from app import __version__
from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import check_db_health
from app.schemas.health import DependencyStatus, HealthResponse, ReadinessResponse

logger = get_logger("app.api.health")
settings = get_settings()

router = APIRouter(tags=["Health & Diagnostics"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Process Liveness Probe",
    description="Returns basic process liveness to confirm the FastAPI server is running.",
)
async def get_health() -> HealthResponse:
    """Liveness check confirming the HTTP application process is responsive."""
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        environment=settings.ENVIRONMENT,
        version=__version__,
        timestamp=datetime.now(timezone.utc),
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses={
        200: {"model": ReadinessResponse, "description": "All dependencies are healthy and ready."},
        503: {"model": ReadinessResponse, "description": "One or more dependencies are unavailable."},
    },
    summary="Dependency Readiness Probe",
    description=(
        "Checks whether the application can reach critical backing infrastructure, "
        "including PostgreSQL. Returns 503 if any required dependency fails."
    ),
)
async def get_readiness() -> Response:
    """Readiness probe verifying active connection to required dependencies."""
    now = datetime.now(timezone.utc)

    # Real database ping
    db_ok, db_err = await check_db_health()
    is_sqlite = "sqlite" in settings.DATABASE_URL

    dependencies = {
        "database": DependencyStatus(
            status="connected" if db_ok else "disconnected",
            engine="sqlite" if is_sqlite else "postgresql",
            error=db_err,
        )
    }

    if db_ok:
        readiness_data = ReadinessResponse(
            status="ready",
            timestamp=now,
            dependencies=dependencies,
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=readiness_data.model_dump(mode="json"),
        )

    readiness_data = ReadinessResponse(
        status="not_ready",
        timestamp=now,
        dependencies=dependencies,
    )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=readiness_data.model_dump(mode="json"),
    )
