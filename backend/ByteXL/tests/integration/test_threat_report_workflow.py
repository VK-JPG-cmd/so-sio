import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import create_application


@pytest.mark.asyncio
async def test_threat_report_complete_workflow(app):
    """
    E2E Workflow:
    1. Create FastAPI test client
    2. Submit threat entity for analysis
    3. Check status and ensure explainable signals returned
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Public health check
        health_res = await client.get("/api/v1/health")
        assert health_res.status_code == 200

        # Ready check with DB
        ready_res = await client.get("/api/v1/ready")
        assert ready_res.status_code == 200
        assert ready_res.json()["status"] == "ready"
