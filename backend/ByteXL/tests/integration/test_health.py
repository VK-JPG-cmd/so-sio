import pytest
from httpx import AsyncClient


async def test_health_endpoint_liveness(client: AsyncClient) -> None:
    """Verify GET /api/v1/health returns 200 OK and expected process liveness payload."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "app_name" in data
    assert "environment" in data
    assert "version" in data
    assert "timestamp" in data

    # Verify that health endpoint is purely a process liveness check and does not claim DB ready
    assert "database" not in data
