import io
import uuid
import zipfile
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.core.logging import RedactionFilter, redact_sensitive_text
from app.core.security import decode_access_token, is_access_token_revoked
from app.models.audit_log import AuditLog
from app.models.enums import AccountStatus, UserRole
from app.models.user import User
from app.repositories.brand_repo import escape_like_wildcards
from app.services.detection.apk_analysis import APKAnalysisService
from app.services.detection.jobs import job_tracker
from app.services.detection.url_analysis import SecureURLAnalysisService
from app.services.otp_provider import MockOTPProvider


async def test_access_token_revocation_on_logout(
    client: AsyncClient, mock_otp: MockOTPProvider
) -> None:
    """Verify that logging out invalidates access token JTIs and prevents subsequent use."""
    phone = "+14155559001"
    await client.post("/api/v1/auth/otp/start", json={"phone_number": phone})
    code = mock_otp.get_last_code(phone)

    login_res = await client.post(
        "/api/v1/auth/otp/verify",
        json={"phone_number": phone, "code": code},
    )
    assert login_res.status_code == 200
    data = login_res.json()
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]

    # Verify token allows fetching profile
    me_res = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_res.status_code == 200

    # Call logout
    logout_res = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"refresh_token": refresh_token},
    )
    assert logout_res.status_code == 200

    # Accessing /users/me with revoked access token must now return 401
    me_revoked_res = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_revoked_res.status_code == 401
    assert "revoked" in me_revoked_res.json()["error"]["message"].lower()


async def test_otp_bruteforce_lockout_persists(
    client: AsyncClient, mock_otp: MockOTPProvider
) -> None:
    """Verify that failed OTP attempts accumulate persistently and lock after maximum attempts."""
    phone = "+14155559002"
    await client.post("/api/v1/auth/otp/start", json={"phone_number": phone})
    valid_code = mock_otp.get_last_code(phone)

    # Submit 5 incorrect codes (max is 5 attempts)
    for _ in range(5):
        fail_res = await client.post(
            "/api/v1/auth/otp/verify",
            json={"phone_number": phone, "code": "000000"},
        )
        assert fail_res.status_code == 400

    # 6th attempt even with valid code must be rejected due to lockout
    locked_res = await client.post(
        "/api/v1/auth/otp/verify",
        json={"phone_number": phone, "code": valid_code},
    )
    assert locked_res.status_code == 400
    err_msg = locked_res.json()["error"]["message"].lower()
    assert "maximum" in err_msg or "expired" in err_msg


async def test_analysis_job_idor_prevention(
    client: AsyncClient, mock_otp: MockOTPProvider
) -> None:
    """Verify that analysis jobs cannot be accessed by unauthorized users (IDOR defense)."""
    # User A
    phone_a = "+14155559003"
    await client.post("/api/v1/auth/otp/start", json={"phone_number": phone_a})
    code_a = mock_otp.get_last_code(phone_a)
    login_a = await client.post(
        "/api/v1/auth/otp/verify", json={"phone_number": phone_a, "code": code_a}
    )
    token_a = login_a.json()["access_token"]
    user_a_id = uuid.UUID(login_a.json()["user"]["id"])

    # User B
    phone_b = "+14155559004"
    await client.post("/api/v1/auth/otp/start", json={"phone_number": phone_b})
    code_b = mock_otp.get_last_code(phone_b)
    login_b = await client.post(
        "/api/v1/auth/otp/verify", json={"phone_number": phone_b, "code": code_b}
    )
    token_b = login_b.json()["access_token"]

    # Create job owned by User A
    job_record = await job_tracker.create_job(
        job_type="apk",
        creator_user_id=user_a_id,
    )

    # User A can view their job
    res_a = await client.get(
        f"/api/v1/analyze/jobs/{job_record.job_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_a.status_code == 200
    assert res_a.json()["job_id"] == str(job_record.job_id)

    # User B must be rejected with 403 Forbidden
    res_b = await client.get(
        f"/api/v1/analyze/jobs/{job_record.job_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_b.status_code == 403
    assert "not have permission" in res_b.json()["error"]["message"].lower() or "forbidden" in res_b.json()["error"]["message"].lower()


def test_ssrf_ip_and_metadata_validation() -> None:
    """Test SSRF validation against integers, IPv4-mapped IPv6, metadata, and loopback."""
    # Cloud metadata hosts
    for meta in ["169.254.169.254", "100.100.100.200", "instance-data", "metadata.google.internal"]:
        res = SecureURLAnalysisService.validate_ip_address(meta)
        assert not res.is_safe_public_ip, f"Failed to reject metadata host {meta}"

    # Integer and hex IPv4 representations of 127.0.0.1
    for loopback_fmt in ["127.0.0.1", "2130706433", "0x7f000001", "017700000001"]:
        res = SecureURLAnalysisService.validate_ip_address(loopback_fmt)
        assert not res.is_safe_public_ip, f"Failed to reject loopback format {loopback_fmt}"

    # IPv4-mapped IPv6
    res = SecureURLAnalysisService.validate_ip_address("::ffff:127.0.0.1")
    assert not res.is_safe_public_ip
    assert res.is_loopback

    res_meta_v6 = SecureURLAnalysisService.validate_ip_address("::ffff:169.254.169.254")
    assert not res_meta_v6.is_safe_public_ip
    assert res_meta_v6.is_cloud_metadata

    # Private domain suffixes
    for priv_domain in ["app.internal", "db.local", "server.localhost", "infra.lan"]:
        res = SecureURLAnalysisService.validate_ip_address(priv_domain)
        assert not res.is_safe_public_ip, f"Failed to reject private domain {priv_domain}"

    # Public IP
    res_pub = SecureURLAnalysisService.validate_ip_address("8.8.8.8")
    assert res_pub.is_safe_public_ip


async def test_apk_streaming_upload_limit(client: AsyncClient, mock_otp: MockOTPProvider) -> None:
    """Test that oversized APK uploads are rejected."""
    phone = "+14155559005"
    await client.post("/api/v1/auth/otp/start", json={"phone_number": phone})
    code = mock_otp.get_last_code(phone)
    login = await client.post(
        "/api/v1/auth/otp/verify", json={"phone_number": phone, "code": code}
    )
    token = login.json()["access_token"]

    # Create dummy payload larger than 50MB (e.g. 51MB)
    oversized_data = b"0" * (51 * 1024 * 1024)
    files = {"file": ("malicious.apk", oversized_data, "application/vnd.android.package-archive")}

    res = await client.post(
        "/api/v1/analyze/apk",
        headers={"Authorization": f"Bearer {token}"},
        files=files,
    )
    assert res.status_code in (400, 413)
    assert "maximum" in res.json()["error"]["message"].lower() or "50 mb" in res.json()["error"]["message"].lower()


def test_apk_zip_bomb_detection() -> None:
    """Test that zip bombs with abnormal decompression expansion are detected and rejected."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("AndroidManifest.xml", b"<manifest></manifest>")
        # Compress 15MB of zeros into classes.dex
        data = b"\x00" * (15 * 1024 * 1024)
        zf.writestr("classes.dex", data)

    buffer.seek(0)
    service = APKAnalysisService()
    # High compression ratio (> 100:1) triggers zip bomb ValidationError
    with pytest.raises(ValidationError, match="potential zip bomb"):
        service.analyze_apk(buffer.getvalue())


def test_apk_path_traversal_detection() -> None:
    """Test that archives with path traversal members are rejected."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.writestr("AndroidManifest.xml", b"<manifest></manifest>")
        zf.writestr("../../etc/passwd", b"root:x:0:0:")

    buffer.seek(0)
    service = APKAnalysisService()
    with pytest.raises(ValidationError, match="Malicious archive member path detected"):
        service.analyze_apk(buffer.getvalue())


def test_sensitive_data_redaction_filter() -> None:
    """Verify that logging redaction removes passwords, tokens, JWTs, and PII."""
    raw_message = (
        "User logged in with phone +14155551234, token Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.xyz, "
        "otp: 987654 and db postgresql+asyncpg://admin:supersecretpwd@db:5432/brandshield"
    )
    sanitized = redact_sensitive_text(raw_message)
    assert "+14155551234" not in sanitized
    assert "supersecretpwd" not in sanitized
    assert "987654" not in sanitized
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in sanitized
    assert "[REDACTED]" in sanitized or "***" in sanitized


async def test_audit_log_immutability(db_session: AsyncSession) -> None:
    """Verify that AuditLog records are append-only and raise PermissionError on update or delete."""
    user = User(
        id=uuid.uuid4(),
        phone_number="+14155559099",
        role=UserRole.ADMIN,
        account_status=AccountStatus.ACTIVE,
    )
    db_session.add(user)
    await db_session.flush()

    log_id = uuid.uuid4()
    log_entry = AuditLog(
        id=log_id,
        actor_user_id=user.id,
        action="brand.verify",
        entity_type="brand",
        entity_id=str(uuid.uuid4()),
        details={"status": "VERIFIED"},
    )
    db_session.add(log_entry)
    await db_session.commit()

    # Try updating the audit log
    log_entry.action = "brand.tampered"
    with pytest.raises(PermissionError, match="strictly immutable and cannot be modified"):
        await db_session.commit()

    await db_session.rollback()

    # Try deleting the audit log
    stmt = select(AuditLog).filter_by(id=log_id)
    res = await db_session.execute(stmt)
    record = res.scalar_one()

    await db_session.delete(record)
    with pytest.raises(PermissionError, match="strictly immutable and cannot be deleted"):
        await db_session.commit()


def test_sql_like_wildcard_escaping() -> None:
    """Verify that SQL LIKE wildcards (% and _) and backslashes are properly escaped."""
    assert escape_like_wildcards("100%_brand\\test") == "100\\%\\_brand\\\\test"
    assert escape_like_wildcards("normal_brand") == "normal\\_brand"
    assert escape_like_wildcards("pure%brand") == "pure\\%brand"
