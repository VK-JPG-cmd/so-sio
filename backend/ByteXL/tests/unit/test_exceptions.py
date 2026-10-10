import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI
from app.core.exceptions import (
    AppException,
    DatabaseConnectionError,
    ResourceNotFoundError,
    setup_exception_handlers,
)


@pytest.fixture
def exception_test_app() -> FastAPI:
    """FastAPI app with routes designed to trigger specific exceptions."""
    app = FastAPI()
    setup_exception_handlers(app)

    @app.get("/trigger-app-exception")
    async def trigger_app_exception() -> None:
        raise AppException(
            message="Custom domain failure",
            status_code=400,
            error_code="CUSTOM_ERROR",
            details={"field": "domain"},
        )

    @app.get("/trigger-db-exception")
    async def trigger_db_exception() -> None:
        raise DatabaseConnectionError("Postgres cluster is partitioned")

    @app.get("/trigger-not-found")
    async def trigger_not_found() -> None:
        raise ResourceNotFoundError("Brand profile #42 not found")

    @app.get("/trigger-unhandled")
    async def trigger_unhandled() -> None:
        raise RuntimeError("Unexpected low-level crash")

    return app


async def test_custom_app_exception_handled(exception_test_app: FastAPI) -> None:
    transport = ASGITransport(app=exception_test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/trigger-app-exception")
        assert response.status_code == 400
        body = response.json()
        assert "error" in body
        assert body["error"]["code"] == "CUSTOM_ERROR"
        assert body["error"]["message"] == "Custom domain failure"
        assert body["error"]["details"] == {"field": "domain"}


async def test_database_connection_exception_handled(exception_test_app: FastAPI) -> None:
    transport = ASGITransport(app=exception_test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/trigger-db-exception")
        assert response.status_code == 503
        body = response.json()
        assert body["error"]["code"] == "DATABASE_UNAVAILABLE"
        assert "Postgres cluster is partitioned" in body["error"]["message"]


async def test_resource_not_found_handled(exception_test_app: FastAPI) -> None:
    transport = ASGITransport(app=exception_test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/trigger-not-found")
        assert response.status_code == 404
        body = response.json()
        assert body["error"]["code"] == "NOT_FOUND"


async def test_unhandled_exception_returns_500_safe_response(
    exception_test_app: FastAPI,
) -> None:
    transport = ASGITransport(app=exception_test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/trigger-unhandled")
        assert response.status_code == 500
        body = response.json()
        assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
        # Should NOT leak internal stack trace in the error message
        assert "Unexpected low-level crash" not in body["error"]["message"]
