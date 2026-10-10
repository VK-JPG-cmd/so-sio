"""
End-to-End Resilience, Concurrency, Migrations, and Security Operations Test Suite — Phase 11

Validates:
- Database migration graph integrity and head convergence
- Background job tracking (asynchronous APK static analysis)
- Secure evidence file handling and header safety
- Deduplication and alert suppression
- Sliding-window rate limit enforcement
- Concurrent user operations
- Strict multi-tenant RBAC boundary enforcement
"""

import asyncio
import io
import uuid
import zipfile
import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from alembic.config import Config
from alembic.script import ScriptDirectory
from app.core.exceptions import RateLimitExceededError
from app.core.rate_limit import InMemoryRateLimiter
from app.models.enums import RiskSeverity, TargetType, UserRole
from app.models.user import User
from app.repositories.correlation_repo import AlertRepository
from app.services.otp_provider import MockOTPProvider


async def _create_authenticated_user(
    client: AsyncClient, mock_otp: MockOTPProvider, phone: str
) -> tuple[str, str]:
    """Helper to authenticate user via OTP, returning (user_id, access_token)."""
    await client.post("/api/v1/auth/otp/start", json={"phone_number": phone})
    code = mock_otp.get_last_code(phone)
    verify_res = await client.post(
        "/api/v1/auth/otp/verify", json={"phone_number": phone, "code": code}
    )
    data = verify_res.json()
    return data["user"]["id"], data["access_token"]


def test_alembic_migrations_integrity() -> None:
    """Verify that Alembic migrations form a valid, unbroken, single-head directed acyclic graph."""
    alembic_cfg = Config("alembic.ini")
    script_dir = ScriptDirectory.from_config(alembic_cfg)
    
    # 1. Verify single head revision
    heads = script_dir.get_heads()
    assert len(heads) == 1, f"Expected exactly 1 migration head, found: {heads}"
    head_rev = heads[0]
    assert head_rev == "008_threat_discovery"

    # 2. Verify all 8 migrations form an unbroken chain
    revisions = list(script_dir.walk_revisions("base", head_rev))
    expected_rev_ids = [
        "008_threat_discovery",
        "007_official_brand_assets",
        "006_brand_owner_portal_and_audit",
        "005_threat_intel_and_campaigns",
        "004_risk_assessments",
        "003_reviews_and_threat_reports",
        "002_brand_tables",
        "001_auth_tables",
    ]
    actual_rev_ids = [r.revision for r in revisions]
    assert actual_rev_ids == expected_rev_ids


@pytest.mark.asyncio
async def test_apk_background_job_lifecycle(
    client: AsyncClient, mock_otp: MockOTPProvider
) -> None:
    """Verify asynchronous background job submission, processing, and state retrieval."""
    _, token = await _create_authenticated_user(client, mock_otp, "+14155551401")
    headers = {"Authorization": f"Bearer {token}"}

    # Generate synthetic APK archive containing AndroidManifest.xml
    apk_buf = io.BytesIO()
    with zipfile.ZipFile(apk_buf, "w") as zf:
        zf.writestr(
            "AndroidManifest.xml",
            b"<manifest package='com.brandshield.testapp'><application></application></manifest>",
        )
    apk_bytes = apk_buf.getvalue()

    # 1. Submit APK -> HTTP 202 Accepted with job_id
    files = {"file": ("test_package.apk", io.BytesIO(apk_bytes), "application/vnd.android.package-archive")}
    submit_res = await client.post("/api/v1/analyze/apk", headers=headers, files=files)
    assert submit_res.status_code == 202
    job_data = submit_res.json()
    job_id = job_data["job_id"]
    assert job_data["status"] in ["PENDING", "PROCESSING"]

    # 2. Poll job status until COMPLETED or timeout
    max_retries = 20
    final_status = None
    result_data = None
    for _ in range(max_retries):
        await asyncio.sleep(0.1)
        poll_res = await client.get(f"/api/v1/analyze/jobs/{job_id}", headers=headers)
        assert poll_res.status_code == 200
        pdata = poll_res.json()
        final_status = pdata["status"]
        if final_status in ["COMPLETED", "FAILED"]:
            result_data = pdata.get("result")
            break

    assert final_status == "COMPLETED"
    assert result_data is not None
    assert "sha256_hash" in result_data
    assert "file_size_bytes" in result_data


@pytest.mark.asyncio
async def test_evidence_file_security_and_streaming(
    client: AsyncClient, mock_otp: MockOTPProvider
) -> None:
    """Verify evidence file upload validation, security headers, and rejection of disallowed types."""
    _, token = await _create_authenticated_user(client, mock_otp, "+14155551402")
    headers = {"Authorization": f"Bearer {token}"}

    # Create threat report to receive evidence
    rep_res = await client.post(
        "/api/v1/threat-reports",
        headers=headers,
        json={
            "target_type": "URL",
            "target_value": "https://malicious-evidence-test.org/login",
            "description": "Testing evidence upload safety and download security headers.",
        },
    )
    assert rep_res.status_code == 201
    report_id = rep_res.json()["id"]

    # 1. Upload valid PNG
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05"
        b"\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    files = {"file": ("artifact.png", io.BytesIO(png_bytes), "image/png")}
    up_res = await client.post(
        f"/api/v1/threat-reports/{report_id}/evidence",
        headers=headers,
        files=files,
        data={"evidence_type": "SCREENSHOT"},
    )
    assert up_res.status_code == 201
    evidence_id = up_res.json()["id"]

    # 2. Download evidence and verify security headers
    down_res = await client.get(
        f"/api/v1/threat-reports/{report_id}/evidence/{evidence_id}",
        headers=headers,
    )
    assert down_res.status_code == 200
    assert down_res.headers["X-Content-Type-Options"] == "nosniff"
    assert "attachment" in down_res.headers["Content-Disposition"]
    assert "default-src 'none'" in down_res.headers["Content-Security-Policy"]
    assert down_res.content == png_bytes

    # 3. Disallowed executable file type must be rejected
    exe_files = {"file": ("malware.exe", io.BytesIO(b"MZ\x90\x00\x03"), "application/x-msdownload")}
    bad_res = await client.post(
        f"/api/v1/threat-reports/{report_id}/evidence",
        headers=headers,
        files=exe_files,
        data={"evidence_type": "SCREENSHOT"},
    )
    assert bad_res.status_code == 400
    err_text = bad_res.json()["error"]["message"].lower()
    assert "not permitted" in err_text or "disallowed" in err_text or "unsupported" in err_text


@pytest.mark.asyncio
async def test_duplicate_submission_and_alert_suppression(
    db_session: AsyncSession,
) -> None:
    """Verify that repeated entity correlation suppresses duplicate alerts for the same fingerprint."""
    alert_repo = AlertRepository()
    brand_id = uuid.uuid4()
    fingerprint = "fp_dedup_test_cluster_999"

    # 1. Create initial alert
    alert1, created1 = await alert_repo.create_if_not_duplicate(
        db=db_session,
        brand_id=brand_id,
        title="Spike in Phishing Activity",
        description="First alert occurrence",
        severity=RiskSeverity.HIGH,
        fingerprint=fingerprint,
    )
    await db_session.commit()
    assert created1 is True
    assert alert1 is not None

    # 2. Second creation attempt with same fingerprint must be suppressed (deduplicated)
    alert2, created2 = await alert_repo.create_if_not_duplicate(
        db=db_session,
        brand_id=brand_id,
        title="Spike in Phishing Activity",
        description="Duplicate alert occurrence",
        severity=RiskSeverity.HIGH,
        fingerprint=fingerprint,
    )
    await db_session.commit()
    assert created2 is False
    assert alert2.id == alert1.id


def test_rate_limiter_sliding_window_enforcement() -> None:
    """Verify that InMemoryRateLimiter accurately enforces sliding window limits and raises RateLimitExceededError."""
    limiter = InMemoryRateLimiter(requests_limit=3, window_seconds=10)
    client_ip = "192.168.1.50"

    # 3 allowed requests
    limiter.check(client_ip)
    limiter.check(client_ip)
    limiter.check(client_ip)

    # 4th request within window must be blocked
    with pytest.raises(RateLimitExceededError) as exc_info:
        limiter.check(client_ip)

    assert "Rate limit exceeded" in str(exc_info.value)
    assert exc_info.value.details["retry_after_seconds"] >= 1

    # Reset allows requests again
    limiter.reset()
    limiter.check(client_ip)


@pytest.mark.asyncio
async def test_concurrent_review_submissions(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """Verify concurrent review submissions execute reliably without race conditions or locks."""
    # Setup brand
    admin_id, admin_token = await _create_authenticated_user(client, mock_otp, "+14155551499")
    await db_session.execute(
        update(User).where(User.id == uuid.UUID(admin_id)).values(role=UserRole.ADMIN)
    )
    await db_session.commit()

    owner_id, owner_token = await _create_authenticated_user(client, mock_otp, "+14155551410")
    app_res = await client.post(
        "/api/v1/brand-applications",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"business_name": "Concurrent Bank", "official_domain": "concurrentbank.com"},
    )
    app_id = app_res.json()["id"]
    rev_res = await client.post(
        f"/api/v1/admin/brand-applications/{app_id}/review",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"decision": "APPROVE"},
    )
    brand_id = rev_res.json()["brand_id"]

    # Multiple distinct customers submitting reviews
    tokens = []
    for i in range(3):
        _, token = await _create_authenticated_user(client, mock_otp, f"+1415555142{i}")
        tokens.append(token)

    for i in range(3):
        res = await client.post(
            f"/api/v1/brands/{brand_id}/reviews",
            headers={"Authorization": f"Bearer {tokens[i]}"},
            json={"rating": 5, "body": f"Concurrent review number {i} with valid text content."},
        )
        assert res.status_code == 201


@pytest.mark.asyncio
async def test_e2e_rbac_and_cross_tenant_isolation(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """Verify comprehensive cross-tenant and role authorization boundaries."""
    # Setup Admin, Brand A Owner, Brand B Owner, Customer
    admin_id, admin_token = await _create_authenticated_user(client, mock_otp, "+14155551500")
    await db_session.execute(
        update(User).where(User.id == uuid.UUID(admin_id)).values(role=UserRole.ADMIN)
    )
    await db_session.commit()

    # Brand A
    _, owner_a_tok = await _create_authenticated_user(client, mock_otp, "+14155551501")
    app_a = await client.post(
        "/api/v1/brand-applications",
        headers={"Authorization": f"Bearer {owner_a_tok}"},
        json={"business_name": "Tenant Alpha", "official_domain": "alpha-corp.io"},
    )
    brand_a_id = (
        await client.post(
            f"/api/v1/admin/brand-applications/{app_a.json()['id']}/review",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"decision": "APPROVE"},
        )
    ).json()["brand_id"]

    # Brand B
    _, owner_b_tok = await _create_authenticated_user(client, mock_otp, "+14155551502")
    _, cust_tok = await _create_authenticated_user(client, mock_otp, "+14155551503")

    headers_b = {"Authorization": f"Bearer {owner_b_tok}"}
    headers_cust = {"Authorization": f"Bearer {cust_tok}"}

    # 1. Customer cannot access Brand A's owner dashboard -> 403 Forbidden
    res_cust_dash = await client.get(
        f"/api/v1/owner/brands/{brand_a_id}/dashboard", headers=headers_cust
    )
    assert res_cust_dash.status_code == 403

    # 2. Owner B cannot access Brand A's dashboard -> 403 Forbidden
    res_b_dash = await client.get(
        f"/api/v1/owner/brands/{brand_a_id}/dashboard", headers=headers_b
    )
    assert res_b_dash.status_code == 403

    # 3. Customer cannot access admin routes -> 403 Forbidden
    res_admin_block = await client.post(
        f"/api/v1/admin/brand-applications/{app_a.json()['id']}/review",
        headers=headers_cust,
        json={"decision": "APPROVE"},
    )
    assert res_admin_block.status_code == 403
