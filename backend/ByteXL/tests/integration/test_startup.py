import pytest
from httpx import ASGITransport, AsyncClient
from app.main import create_application


async def test_application_startup_and_openapi_docs() -> None:
    """Verify application starts, generates OpenAPI documentation, and serves docs."""
    app = create_application()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Check docs
        response = await client.get("/docs")
        assert response.status_code == 200

        # Check openapi.json
        openapi_res = await client.get("/openapi.json")
        assert openapi_res.status_code == 200
        schema = openapi_res.json()
        assert schema["info"]["title"] == "BrandShield AI Backend"
        assert "/api/v1/health" in schema["paths"]
        assert "/api/v1/ready" in schema["paths"]


async def test_cors_middleware_headers() -> None:
    """Verify CORS preflight and response headers for configured origins."""
    app = create_application()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
