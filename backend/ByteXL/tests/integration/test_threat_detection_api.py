"""
Integration tests for Threat Detection Engine API endpoints:
- POST /api/v1/analyze/text
- POST /api/v1/analyze/url
- POST /api/v1/analyze/profile
- POST /api/v1/analyze/apk (HTTP 202 Accepted)
- GET /api/v1/analyze/jobs/{job_id}
- Authentication & input validation boundaries
"""

import asyncio
import io
import uuid
import zipfile
import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.enums import UserRole
from app.models.user import User
from app.services.otp_provider import MockOTPProvider


async def _create_user(
    client: AsyncClient, mock_otp: MockOTPProvider, phone: str
) -> tuple[str, str]:
    """Helper to authenticate a user via OTP returning (user_id, access_token)."""
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
    """Helper to authenticate a user and promote them to ADMIN."""
    user_id, token = await _create_user(client, mock_otp, phone)
    await db_session.execute(
        update(User).where(User.id == uuid.UUID(user_id)).values(role=UserRole.ADMIN)
    )
    await db_session.commit()
    return user_id, token


async def _setup_verified_brand(
    client: AsyncClient,
    mock_otp: MockOTPProvider,
    admin_token: str,
    phone: str,
    domain: str = "acmepayments.com",
) -> str:
    """Helper to register and administratively approve a brand."""
    _, owner_token = await _create_user(client, mock_otp, phone)
    app_res = await client.post(
        "/api/v1/brand-applications",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"business_name": "Acme Payments Corp", "official_domain": domain},
    )
    app_id = app_res.json()["id"]

    review_res = await client.post(
        f"/api/v1/admin/brand-applications/{app_id}/review",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"decision": "APPROVE", "notes": "Verified business entity"},
    )
    return str(review_res.json()["brand_id"])


def _generate_synthetic_apk() -> bytes:
    """Helper to generate a minimal synthetically packaged APK zip."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("AndroidManifest.xml", b"<manifest package='com.acme.phish'></manifest>")
        zf.writestr("classes.dex", b"dex\n035\x00")
    return buf.getvalue()


# ============================================================================
# 1. TEXT ANALYSIS ENDPOINT
# ============================================================================


async def test_analyze_text_scam_detection(
    client: AsyncClient, mock_otp: MockOTPProvider
) -> None:
    """Verify POST /api/v1/analyze/text evaluates scam probability and indicators."""
    _, token = await _create_user(client, mock_otp, "+14155558001")

    res = await client.post(
        "/api/v1/analyze/text",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "text": "URGENT: Your account has been suspended! Send $200 in bitcoin to http://scam-restore.link now."
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_scam"] is True
    assert data["scam_probability"] >= 0.60
    assert len(data["urgency_indicators"]) > 0
    assert len(data["financial_indicators"]) > 0
    assert data["model_metadata"]["model_version"] == "0.1.0-baseline-dev"


async def test_analyze_text_benign_message(
    client: AsyncClient, mock_otp: MockOTPProvider
) -> None:
    """Verify clean support message receives low risk score."""
    _, token = await _create_user(client, mock_otp, "+14155558002")

    res = await client.post(
        "/api/v1/analyze/text",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "text": "Hello, your order has shipped and will arrive on Friday. Thank you for shopping with us."
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_scam"] is False
    assert data["risk_level"] == "LOW"


# ============================================================================
# 2. URL ANALYSIS ENDPOINT & SSRF DEFENSES
# ============================================================================


async def test_analyze_url_ssrf_blocked(
    client: AsyncClient, mock_otp: MockOTPProvider
) -> None:
    """Verify private and cloud metadata URLs are flagged and blocked from outbound requests."""
    _, token = await _create_user(client, mock_otp, "+14155558003")

    # AWS metadata endpoint
    res_meta = await client.post(
        "/api/v1/analyze/url",
        headers={"Authorization": f"Bearer {token}"},
        json={"url": "http://169.254.169.254/latest/meta-data/"},
    )
    assert res_meta.status_code == 200
    data = res_meta.json()
    assert data["is_ssrf_blocked"] is True
    assert "metadata" in data["ssrf_block_reason"].lower()
    assert data["risk_score"] == 100.0

    # Localhost loopback
    res_loop = await client.post(
        "/api/v1/analyze/url",
        headers={"Authorization": f"Bearer {token}"},
        json={"url": "http://127.0.0.1:8000/internal-admin"},
    )
    assert res_loop.status_code == 200
    assert res_loop.json()["is_ssrf_blocked"] is True


async def test_analyze_url_brand_impersonation(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """Verify URL mimicking a verified brand receives high similarity and risk scores."""
    _, admin_token = await _create_admin(client, mock_otp, "+14155558004", db_session)
    brand_id = await _setup_verified_brand(client, mock_otp, admin_token, "+14155558005", "acmepayments.com")
    _, cust_token = await _create_user(client, mock_otp, "+14155558006")

    res = await client.post(
        "/api/v1/analyze/url",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={
            "url": "https://acmepayments-login-verify.com/auth/login?token=abc",
            "brand_id": brand_id,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["domain_analysis"]["matched_brand_name"] == "Acme Payments Corp"
    assert data["domain_analysis"]["similarity_score"] > 60.0
    assert data["risk_level"] in ("HIGH", "CRITICAL")
    assert "SAFE_OFFLINE_ANALYSIS" in data["fetch_policy"]


# ============================================================================
# 3. SOCIAL PROFILE ANALYSIS ENDPOINT
# ============================================================================


async def test_analyze_profile_impersonation_and_fair_scoring(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """
    Verify profile analysis:
    - Homoglyph/typosquat username + bio claims -> high risk.
    - Missing optional profile fields does NOT penalize or inflate risk score.
    """
    _, admin_token = await _create_admin(client, mock_otp, "+14155558007", db_session)
    brand_id = await _setup_verified_brand(client, mock_otp, admin_token, "+14155558008", "trustedcorp.com")
    _, cust_token = await _create_user(client, mock_otp, "+14155558009")

    # 1. High-risk profile spoof
    res_spoof = await client.post(
        "/api/v1/analyze/profile",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={
            "platform": "Twitter",
            "username": "@acmepayments_help",
            "display_name": "Acme Payments Support",
            "bio": "Official Customer Support for Acme Payments. DM us for account recovery.",
            "external_links": ["http://acme-support-desk.top"],
            "brand_id": brand_id,
        },
    )
    assert res_spoof.status_code == 200
    data_spoof = res_spoof.json()
    assert data_spoof["username_similarity"] > 70.0
    assert data_spoof["bio_impersonation_detected"] is True
    assert data_spoof["profile_link_mismatch"] is True
    assert data_spoof["risk_level"] in ("HIGH", "CRITICAL")

    # 2. Minimal profile with missing optional fields -> fair baseline
    res_minimal = await client.post(
        "/api/v1/analyze/profile",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={
            "platform": "Twitter",
            "username": "@random_gardener_99",
            # bio, display_name, external_links are omitted
        },
    )
    assert res_minimal.status_code == 200
    data_min = res_minimal.json()
    # Missing fields must not increase risk score
    assert data_min["risk_score"] == 0.0
    assert data_min["risk_level"] == "LOW"


# ============================================================================
# 4. APK STATIC ANALYSIS & JOB TRACKING ENDPOINTS
# ============================================================================


async def test_analyze_apk_job_workflow(
    client: AsyncClient, mock_otp: MockOTPProvider
) -> None:
    """
    Verify APK analysis asynchronous lifecycle:
    - POST /api/v1/analyze/apk returns HTTP 202 Accepted with job_id.
    - GET /api/v1/analyze/jobs/{job_id} tracks real progress and completed results.
    - Background task genuinely executed without faking completion.
    """
    _, cust_token = await _create_user(client, mock_otp, "+14155558010")
    apk_content = _generate_synthetic_apk()

    # Submit APK for static analysis
    post_res = await client.post(
        "/api/v1/analyze/apk",
        headers={"Authorization": f"Bearer {cust_token}"},
        files={"file": ("fake_app.apk", apk_content, "application/vnd.android.package-archive")},
    )
    assert post_res.status_code == 202
    job_info = post_res.json()
    assert "job_id" in job_info
    assert job_info["job_type"] == "APK_STATIC_ANALYSIS"
    assert job_info["status"] in ("PENDING", "PROCESSING")
    job_id = job_info["job_id"]

    # Poll job status (allow brief execution time in worker thread)
    completed_data = None
    for _ in range(20):
        poll_res = await client.get(
            f"/api/v1/analyze/jobs/{job_id}",
            headers={"Authorization": f"Bearer {cust_token}"},
        )
        assert poll_res.status_code == 200
        poll_data = poll_res.json()
        if poll_data["status"] == "COMPLETED":
            completed_data = poll_data
            break
        await asyncio.sleep(0.1)

    assert completed_data is not None
    assert completed_data["status"] == "COMPLETED"
    assert completed_data["result"] is not None
    assert completed_data["result"]["file_name"] == "fake_app.apk"
    assert completed_data["result"]["is_valid_apk"] is True
    assert completed_data["completed_at"] is not None


# ============================================================================
# 5. AUTHENTICATION BOUNDARIES
# ============================================================================


async def test_unauthorized_analysis_requests_rejected(client: AsyncClient) -> None:
    """Verify unauthenticated requests return 401 Unauthorized."""
    # Text analysis
    res_text = await client.post("/api/v1/analyze/text", json={"text": "Hello"})
    assert res_text.status_code == 401

    # URL analysis
    res_url = await client.post("/api/v1/analyze/url", json={"url": "https://example.com"})
    assert res_url.status_code == 401

    # Profile analysis
    res_prof = await client.post("/api/v1/analyze/profile", json={"platform": "Twitter", "username": "user"})
    assert res_prof.status_code == 401

    # Job status
    res_job = await client.get(f"/api/v1/analyze/jobs/{uuid.uuid4()}")
    assert res_job.status_code == 401
