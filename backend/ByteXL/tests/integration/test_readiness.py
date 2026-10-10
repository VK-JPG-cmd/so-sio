from unittest.mock import patch
import pytest
from httpx import AsyncClient
from app.db.session import check_db_health


async def test_readiness_healthy_when_database_connected(client: AsyncClient) -> None:
    """Verify /api/v1/ready returns 200 OK and connected status when database is reachable."""
    with patch(
        "app.api.v1.endpoints.health.check_db_health",
        return_value=(True, None),
    ):
        response = await client.get("/api/v1/ready")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ready"
        assert "timestamp" in data
        assert "database" in data["dependencies"]
        assert data["dependencies"]["database"]["status"] == "connected"
        assert data["dependencies"]["database"]["engine"] == "postgresql"
        assert data["dependencies"]["database"]["error"] is None


async def test_readiness_fails_503_when_database_unreachable(client: AsyncClient) -> None:
    """Verify /api/v1/ready returns 503 Service Unavailable when database connection fails."""
    simulated_error = "ConnectionRefusedError: Connection to postgres:5432 refused"
    with patch(
        "app.api.v1.endpoints.health.check_db_health",
        return_value=(False, simulated_error),
    ):
        response = await client.get("/api/v1/ready")
        assert response.status_code == 503

        data = response.json()
        assert data["status"] == "not_ready"
        assert "timestamp" in data
        assert "database" in data["dependencies"]
        assert data["dependencies"]["database"]["status"] == "disconnected"
        assert data["dependencies"]["database"]["engine"] == "postgresql"
        assert simulated_error in data["dependencies"]["database"]["error"]


async def test_real_database_probe_reports_actual_status(client: AsyncClient) -> None:
    """
    Verify real database probe directly.
    If PostgreSQL is offline, check_db_health must return (False, error) and readiness returns 503.
    Never silently assumes true.
    """
    is_connected, error = await check_db_health(timeout_seconds=1.0)
    response = await client.get("/api/v1/ready")

    if is_connected:
        assert response.status_code == 200
        assert response.json()["status"] == "ready"
    else:
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["dependencies"]["database"]["status"] == "disconnected"
        assert data["dependencies"]["database"]["error"] is not None
