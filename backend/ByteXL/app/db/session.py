import asyncio
from typing import AsyncGenerator, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("app.db.session")
settings = get_settings()

# Asynchronous SQLAlchemy 2.x Engine
is_sqlite = "sqlite" in settings.DATABASE_URL

if is_sqlite:
    engine: AsyncEngine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )
else:
    engine: AsyncEngine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency yielding a managed async database session.
    Commits on normal completion, rolls back on exception, and ensures closure.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_health(timeout_seconds: float = 3.0) -> Tuple[bool, Optional[str]]:
    """
    Verify real PostgreSQL connectivity by executing a lightweight query.
    Returns (is_connected: bool, error_message: Optional[str]).
    Never assumes success without an active network response.
    """
    try:
        async def _ping() -> None:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

        await asyncio.wait_for(_ping(), timeout=timeout_seconds)
        return True, None
    except asyncio.TimeoutError:
        error_msg = f"Database health check timed out after {timeout_seconds}s"
        logger.warning(error_msg)
        return False, error_msg
    except Exception as exc:
        error_msg = f"{type(exc).__name__}: {str(exc)}"
        logger.warning(f"Database health check failed: {error_msg}")
        return False, error_msg


async def close_db_engine() -> None:
    """Safely dispose of connection pools on application shutdown."""
    await engine.dispose()
