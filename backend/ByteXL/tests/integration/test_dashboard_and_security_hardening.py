"""
Phase 7 Integration Tests: Dashboard Integration, Security Hardening, and RBAC
Validates:
1. Command Center Dashboard endpoints (/ and /dashboard) returning rich HTML
2. Global security headers (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection)
3. RBAC on /admin/discovery/indicators (401 unauth, 403 customer, 200 admin)
4. Application lifespan startup and shutdown with discovery worker disabled and enabled
"""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.main import create_application, lifespan
from app.models.enums import UserRole
from app.models.user import User
from app.services.otp_provider import MockOTPProvider


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _create_user(
    client: AsyncClient, mock_otp: MockOTPProvider, phone: str
) -> tuple[str, str]:
    """Authenticate a user via OTP and return (user_id, token)."""
    await client.post("/api/v1/auth/otp/start", json={"phone_number": phone})
    code = mock_otp.get_last_code(phone)
    verify_res = await client.post(
        "/api/v1/auth/otp/verify", json={"phone_number": phone, "code": code}
    )
    data = verify_res.json()
    return data["user"]["id"], data["access_token"]


async def _create_admin(
    client: AsyncClient,
    mock_otp: MockOTPProvider,
    phone: str,
    db_session: AsyncSession,
) -> tuple[str, str]:
    """Authenticate and promote a user to ADMIN."""
    user_id, token = await _create_user(client, mock_otp, phone)
    await db_session.execute(
        update(User).where(User.id == uuid.UUID(user_id)).values(role=UserRole.ADMIN)
    )
    await db_session.commit()
    return user_id, token


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dashboard_html_endpoints_render_successfully(client: AsyncClient) -> None:
    """Verify that root / and /dashboard routes serve the command center UI."""
    for path in ("/", "/dashboard"):
        res = await client.get(path)
        assert res.status_code == 200, res.text
        assert "text/html" in res.headers.get("content-type", "")
        assert "BrandShield AI" in res.text
        assert "Digital Risk Protection" in res.text
        assert "Threat Discovery Engine" in res.text


@pytest.mark.asyncio
async def test_global_security_headers_enforced(client: AsyncClient) -> None:
    """Verify that protective security headers are attached to HTTP responses."""
    res = await client.get("/api/v1/health")
    assert res.status_code == 200
    headers = res.headers

    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert "1; mode=block" in headers.get("x-xss-protection", "")
    assert "strict-origin-when-cross-origin" in headers.get("referrer-policy", "")


@pytest.mark.asyncio
async def test_admin_discovery_indicators_rbac_and_data(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """
    Verify RBAC on GET /admin/discovery/indicators:
    - Unauthenticated: 401
    - Customer: 403
    - Admin: 200 with list
    """
    # 1. Unauthenticated
    unauth_res = await client.get("/api/v1/admin/discovery/indicators")
    assert unauth_res.status_code == 401

    # 2. Customer
    _, cust_token = await _create_user(client, mock_otp, "+15550007001")
    cust_res = await client.get(
        "/api/v1/admin/discovery/indicators",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert cust_res.status_code == 403

    # 3. Admin
    _, admin_token = await _create_admin(client, mock_otp, "+15550007002", db_session)
    admin_res = await client.get(
        "/api/v1/admin/discovery/indicators?limit=10",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_res.status_code == 200, admin_res.text
    assert isinstance(admin_res.json(), list)


@pytest.mark.asyncio
async def test_application_lifespan_startup_and_shutdown() -> None:
    """
    Verify application lifespan manages startup and shutdown cleanly
    without leaks or crashing when worker is enabled or disabled.
    """
    test_app = create_application()

    # 1. Lifespan with discovery worker disabled (default)
    async with lifespan(test_app):
        from app.services.discovery.worker import discovery_worker
        assert discovery_worker.is_running is False

    # 2. Lifespan with discovery worker enabled
    settings = get_settings()
    original_enabled = settings.THREAT_DISCOVERY_WORKER_ENABLED
    try:
        settings.THREAT_DISCOVERY_WORKER_ENABLED = True
        async with lifespan(test_app):
            from app.services.discovery.worker import discovery_worker
            assert discovery_worker.is_running is True

        # After lifespan exit, worker must be stopped
        assert discovery_worker.is_running is False
    finally:
        settings.THREAT_DISCOVERY_WORKER_ENABLED = original_enabled
