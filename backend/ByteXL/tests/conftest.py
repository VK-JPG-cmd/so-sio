import os

# Ensure test environment defaults
os.environ["ENVIRONMENT"] = "test"
os.environ["DNS_RESOLVER_MODE"] = "mock"
os.environ["OTP_PROVIDER"] = "mock"

from typing import AsyncGenerator
import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
get_settings.cache_clear()

from app.db.base import Base
from app.db.session import get_db
from app.main import create_application
from app.services.dns_resolver import MockDNSResolver, get_dns_resolver
from app.services.otp_provider import MockOTPProvider, get_otp_provider


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Isolated in-memory database session fixture for API integration tests."""
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_maker() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest.fixture
def app(db_session: AsyncSession) -> FastAPI:
    """Fixture providing a test instance of the FastAPI application with bound test DB."""
    application = create_application()

    async def _get_test_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    application.dependency_overrides[get_db] = _get_test_db
    return application


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Fixture providing an async HTTP client bound to the FastAPI application."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
def mock_otp() -> MockOTPProvider:
    """Fixture providing direct access to the mock OTP delivery store."""
    provider = get_otp_provider()
    if isinstance(provider, MockOTPProvider):
        provider.clear()
        return provider
    raise RuntimeError("MockOTPProvider must be active in test environment.")


@pytest.fixture
def mock_dns() -> MockDNSResolver:
    """Fixture providing access to the mock DNS resolver store for simulating TXT records."""
    resolver = get_dns_resolver()
    if isinstance(resolver, MockDNSResolver):
        resolver.clear()
        return resolver
    raise RuntimeError("MockDNSResolver must be active in test environment.")
