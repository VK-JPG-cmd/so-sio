from datetime import datetime
import io
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.models.enums import UserRole
from app.models.user import User
from app.services.otp_provider import MockOTPProvider


async def _create_user(
    client: AsyncClient, mock_otp: MockOTPProvider, phone: str
) -> tuple[str, str]:
    """Helper to authenticate a user via OTP and return (user_id, access_token)."""
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
    """Helper to authenticate a user and promote them to ADMIN role."""
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
    phone: str = "+14155557001",
    domain: str = "securebrand.com",
) -> str:
    """Helper to register and administratively approve a brand, returning its brand_id."""
    _, owner_token = await _create_user(client, mock_otp, phone)
    app_res = await client.post(
        "/api/v1/brand-applications",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"business_name": "Secure Brand Inc", "official_domain": domain},
    )
    app_id = app_res.json()["id"]

    # Admin approves application to create verified brand
    review_res = await client.post(
        f"/api/v1/admin/brand-applications/{app_id}/review",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"decision": "APPROVE", "notes": "Verified business entity"},
    )
    assert review_res.status_code == 200
    return str(review_res.json()["brand_id"])


# ============================================================================
# 1. VALID REVIEWS & MODERATION WORKFLOW
# ============================================================================


async def test_valid_review_submission_and_public_distinction(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """
    Verify customer review submission:
    - Submits with rating and body.
    - Status starts as PENDING_MODERATION.
    - Visible in author's /users/me/reviews.
    - Omitted from public /brands/{brand_id}/reviews until published.
    """
    _, admin_token = await _create_admin(client, mock_otp, "+14155557002", db_session)
    brand_id = await _setup_verified_brand(client, mock_otp, admin_token, "+14155557003", "brand-alpha.com")

    # Customer submits a review
    cust_id, cust_token = await _create_user(client, mock_otp, "+14155557004")
    review_res = await client.post(
        f"/api/v1/brands/{brand_id}/reviews",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={
            "rating": 5,
            "body": "Excellent security compliance and authentic digital identity.",
        },
    )
    assert review_res.status_code == 201
    review_data = review_res.json()
    assert review_data["rating"] == 5
    assert review_data["status"] == "PENDING_MODERATION"
    assert review_data["brand_id"] == brand_id
    assert review_data["customer_id"] == cust_id
    review_id = review_data["id"]

    # Customer views their own reviews -> visible with PENDING_MODERATION
    me_reviews_res = await client.get(
        "/api/v1/users/me/reviews",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert me_reviews_res.status_code == 200
    me_reviews = me_reviews_res.json()
    assert len(me_reviews) == 1
    assert me_reviews[0]["id"] == review_id
    assert me_reviews[0]["status"] == "PENDING_MODERATION"

    # Public brand reviews endpoint -> unmoderated review is NOT visible publicly
    public_res = await client.get(f"/api/v1/brands/{brand_id}/reviews")
    assert public_res.status_code == 200
    assert len(public_res.json()) == 0


async def test_review_moderation_and_negative_reviews(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """
    Verify review moderation:
    - Negative review (1 star) is not automatically classified as fake/malicious.
    - Admin publishes review -> becomes visible publicly.
    - Public review endpoint does not leak customer ID or phone number.
    """
    _, admin_token = await _create_admin(client, mock_otp, "+14155557005", db_session)
    brand_id = await _setup_verified_brand(client, mock_otp, admin_token, "+14155557006", "brand-beta.com")

    _, cust_token = await _create_user(client, mock_otp, "+14155557007")

    # Submit honest negative review
    neg_res = await client.post(
        f"/api/v1/brands/{brand_id}/reviews",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={
            "rating": 1,
            "body": "Slow customer service response during a recent account inquiry.",
        },
    )
    assert neg_res.status_code == 201
    assert neg_res.json()["status"] == "PENDING_MODERATION"
    review_id = neg_res.json()["id"]

    # Admin publishes the honest negative review
    mod_res = await client.patch(
        f"/api/v1/reviews/{review_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "PUBLISHED"},
    )
    assert mod_res.status_code == 200
    assert mod_res.json()["status"] == "PUBLISHED"

    # Now publicly discoverable
    pub_res = await client.get(f"/api/v1/brands/{brand_id}/reviews")
    assert pub_res.status_code == 200
    pub_list = pub_res.json()
    assert len(pub_list) == 1
    assert pub_list[0]["id"] == review_id
    assert pub_list[0]["rating"] == 1
    # Check that private customer identifiers are NOT exposed in public review schema
    assert "customer_id" not in pub_list[0]
    assert "phone" not in str(pub_list[0]).lower()


# ============================================================================
# 2. INVALID RATINGS & INPUT VALIDATION
# ============================================================================


async def test_invalid_ratings_and_lengths_rejected(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """Verify ratings outside 1-5 and invalid body lengths are rejected with 422."""
    _, admin_token = await _create_admin(client, mock_otp, "+14155557008", db_session)
    brand_id = await _setup_verified_brand(client, mock_otp, admin_token, "+14155557009", "brand-gamma.com")
    _, cust_token = await _create_user(client, mock_otp, "+14155557010")

    # Rating = 0 (too low)
    res_zero = await client.post(
        f"/api/v1/brands/{brand_id}/reviews",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={"rating": 0, "body": "This product was average and okay."},
    )
    assert res_zero.status_code == 422

    # Rating = 6 (too high)
    res_six = await client.post(
        f"/api/v1/brands/{brand_id}/reviews",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={"rating": 6, "body": "This product was average and okay."},
    )
    assert res_six.status_code == 422

    # Body too short (< 10 chars)
    res_short = await client.post(
        f"/api/v1/brands/{brand_id}/reviews",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={"rating": 4, "body": "Too short"},
    )
    assert res_short.status_code == 422


# ============================================================================
# 3. REVIEW OWNERSHIP
# ============================================================================


async def test_review_ownership_and_unauthorized_edits(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """
    Verify review ownership enforcement:
    - Author can update their own review (status reverts to PENDING_MODERATION).
    - Another customer is forbidden from editing (403 Forbidden).
    """
    _, admin_token = await _create_admin(client, mock_otp, "+14155557011", db_session)
    brand_id = await _setup_verified_brand(client, mock_otp, admin_token, "+14155557012", "brand-delta.com")

    _, cust_a_token = await _create_user(client, mock_otp, "+14155557013")
    _, cust_b_token = await _create_user(client, mock_otp, "+14155557014")

    # Customer A creates review
    create_res = await client.post(
        f"/api/v1/brands/{brand_id}/reviews",
        headers={"Authorization": f"Bearer {cust_a_token}"},
        json={"rating": 3, "body": "Initial honest assessment of their delivery."},
    )
    review_id = create_res.json()["id"]

    # Customer B attempts to modify Customer A's review -> 403 Forbidden
    hack_res = await client.patch(
        f"/api/v1/reviews/{review_id}",
        headers={"Authorization": f"Bearer {cust_b_token}"},
        json={"rating": 1, "body": "Malicious tampering attempt from another user."},
    )
    assert hack_res.status_code == 403
    assert hack_res.json()["error"]["code"] == "ACCESS_FORBIDDEN"

    # Customer A updates their own review -> 200 OK
    update_res = await client.patch(
        f"/api/v1/reviews/{review_id}",
        headers={"Authorization": f"Bearer {cust_a_token}"},
        json={"rating": 4, "body": "Updated review: delivery arrived in good condition."},
    )
    assert update_res.status_code == 200
    assert update_res.json()["rating"] == 4
    assert update_res.json()["status"] == "PENDING_MODERATION"


async def test_brand_owner_role_forbidden_from_reviews_and_threat_reports(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """Verify that a user with BRAND_OWNER role cannot create customer reviews or threat reports."""
    _, admin_token = await _create_admin(client, mock_otp, "+14155557050", db_session)
    brand_id = await _setup_verified_brand(client, mock_otp, admin_token, "+14155557051", "brand-omega.com")

    # Create a brand owner user
    bowner_id, bowner_token = await _create_user(client, mock_otp, "+14155557052")
    await db_session.execute(
        update(User).where(User.id == uuid.UUID(bowner_id)).values(role=UserRole.BRAND_OWNER)
    )
    await db_session.commit()

    # Brand owner attempts to submit customer review -> 403 Forbidden
    rev_res = await client.post(
        f"/api/v1/brands/{brand_id}/reviews",
        headers={"Authorization": f"Bearer {bowner_token}"},
        json={"rating": 5, "body": "Attempted self-review by brand owner."},
    )
    assert rev_res.status_code == 403
    assert rev_res.json()["error"]["code"] == "ACCESS_FORBIDDEN"

    # Brand owner attempts to submit customer threat report -> 403 Forbidden
    rep_res = await client.post(
        "/api/v1/threat-reports",
        headers={"Authorization": f"Bearer {bowner_token}"},
        json={
            "target_type": "DOMAIN",
            "target_value": "scam-domain.com",
            "description": "Attempted report by non-customer user.",
        },
    )
    assert rep_res.status_code == 403
    assert rep_res.json()["error"]["code"] == "ACCESS_FORBIDDEN"


# ============================================================================
# 4. THREAT REPORT SUBMISSION & OWNERSHIP
# ============================================================================



async def test_threat_report_submission_and_normalization(
    client: AsyncClient, mock_otp: MockOTPProvider
) -> None:
    """Verify threat report submission normalizes domain targets and records status."""
    _, cust_token = await _create_user(client, mock_otp, "+14155557015")

    # Submit DOMAIN threat report
    res_domain = await client.post(
        "/api/v1/threat-reports",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={
            "target_type": "DOMAIN",
            "target_value": "HTTPS://Phishing-Acme-Support.COM/",
            "description": "Impersonation domain serving credential harvesting forms targeting customers.",
        },
    )
    assert res_domain.status_code == 201
    data = res_domain.json()
    assert data["target_type"] == "DOMAIN"
    assert data["target_value"] == "phishing-acme-support.com"  # Normalized FQDN
    assert data["status"] == "SUBMITTED"
    assert "id" in data

    # Submit URL threat report
    res_url = await client.post(
        "/api/v1/threat-reports",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={
            "target_type": "URL",
            "target_value": "https://suspicious-site.org/login.php?brand=fake",
            "description": "Deep phishing URL linked from unsolicited SMS message.",
        },
    )
    assert res_url.status_code == 201


async def test_threat_report_ownership_and_isolation(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """
    Verify customer threat report privacy:
    - User A cannot view User B's report (403 Forbidden).
    - User A's /me/threat-reports contains only their reports.
    - Admin can inspect reports for investigation.
    """
    _, cust_a_token = await _create_user(client, mock_otp, "+14155557016")
    _, cust_b_token = await _create_user(client, mock_otp, "+14155557017")
    _, admin_token = await _create_admin(client, mock_otp, "+14155557018", db_session)

    # Customer A submits report
    rep_a = await client.post(
        "/api/v1/threat-reports",
        headers={"Authorization": f"Bearer {cust_a_token}"},
        json={
            "target_type": "SCAM_TEXT",
            "target_value": "SMS message: 'Your account is locked, click http://scam.link'",
            "description": "Received suspicious SMS spoofing bank security alerts.",
        },
    )
    report_a_id = rep_a.json()["id"]

    # Customer B attempts to view Customer A's report -> 403 Forbidden
    res_b_view = await client.get(
        f"/api/v1/threat-reports/{report_a_id}",
        headers={"Authorization": f"Bearer {cust_b_token}"},
    )
    assert res_b_view.status_code == 403
    assert res_b_view.json()["error"]["code"] == "ACCESS_FORBIDDEN"

    # Customer A views their own report -> 200 OK
    res_a_view = await client.get(
        f"/api/v1/threat-reports/{report_a_id}",
        headers={"Authorization": f"Bearer {cust_a_token}"},
    )
    assert res_a_view.status_code == 200
    assert res_a_view.json()["id"] == report_a_id

    # Admin views report -> 200 OK
    res_admin_view = await client.get(
        f"/api/v1/threat-reports/{report_a_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin_view.status_code == 200

    # Customer B checks their own list -> report A is not in it
    b_list = await client.get(
        "/api/v1/users/me/threat-reports",
        headers={"Authorization": f"Bearer {cust_b_token}"},
    )
    assert len(b_list.json()) == 0


async def test_threat_report_status_tracking(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """Verify threat report investigation status lifecycle transitions by admin."""
    _, cust_token = await _create_user(client, mock_otp, "+14155557019")
    _, admin_token = await _create_admin(client, mock_otp, "+14155557020", db_session)

    rep = await client.post(
        "/api/v1/threat-reports",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={
            "target_type": "MOBILE_APP",
            "target_value": "com.fraudulent.brandapp",
            "description": "Rogue APK impersonating brand application on third-party store.",
        },
    )
    report_id = rep.json()["id"]

    # Non-admin cannot transition report status -> 403
    cust_patch = await client.patch(
        f"/api/v1/threat-reports/{report_id}",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={"status": "CONFIRMED"},
    )
    assert cust_patch.status_code == 403

    # Admin updates status to ANALYZING
    p1 = await client.patch(
        f"/api/v1/threat-reports/{report_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "ANALYZING"},
    )
    assert p1.status_code == 200
    assert p1.json()["status"] == "ANALYZING"

    # Admin confirms threat
    p2 = await client.patch(
        f"/api/v1/threat-reports/{report_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "CONFIRMED"},
    )
    assert p2.status_code == 200
    assert p2.json()["status"] == "CONFIRMED"


# ============================================================================
# 5. EVIDENCE UPLOADS, FILE SECURITY, PATH TRAVERSAL, ACCESS CONTROL
# ============================================================================


async def test_evidence_valid_upload_and_sha256(
    client: AsyncClient, mock_otp: MockOTPProvider
) -> None:
    """Verify valid evidence upload computes SHA-256 and isolates storage."""
    _, cust_token = await _create_user(client, mock_otp, "+14155557021")

    rep = await client.post(
        "/api/v1/threat-reports",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={
            "target_type": "DOMAIN",
            "target_value": "fake-portal.com",
            "description": "Hosting fake credential login page.",
        },
    )
    report_id = rep.json()["id"]

    # Valid PNG content with genuine magic bytes
    valid_png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
    )

    upload_res = await client.post(
        f"/api/v1/threat-reports/{report_id}/evidence",
        headers={"Authorization": f"Bearer {cust_token}"},
        files={"file": ("screenshot.png", valid_png_bytes, "image/png")},
        data={"evidence_type": "SCREENSHOT"},
    )
    assert upload_res.status_code == 201
    data = upload_res.json()
    assert data["report_id"] == report_id
    assert data["original_filename"] == "screenshot.png"
    assert data["file_size"] == len(valid_png_bytes)
    assert len(data["sha256"]) == 64
    assert "evidence/" in data["storage_key"]


async def test_evidence_file_type_restrictions_and_magic_bytes(
    client: AsyncClient, mock_otp: MockOTPProvider
) -> None:
    """
    Verify security restrictions on evidence files:
    - Executable extensions (.exe, .sh) are rejected.
    - Disguised files (wrong magic bytes) are rejected even with valid extension.
    """
    _, cust_token = await _create_user(client, mock_otp, "+14155557022")

    rep = await client.post(
        "/api/v1/threat-reports",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={
            "target_type": "URL",
            "target_value": "https://malicious.link/payload",
            "description": "Distributing malware.",
        },
    )
    report_id = rep.json()["id"]

    # 1. Disallowed extension: .exe
    res_exe = await client.post(
        f"/api/v1/threat-reports/{report_id}/evidence",
        headers={"Authorization": f"Bearer {cust_token}"},
        files={"file": ("malware.exe", b"MZ\x90\x00\x03\x00", "application/octet-stream")},
    )
    assert res_exe.status_code == 400
    assert "not permitted" in res_exe.json()["error"]["message"]

    # 2. Disguised file: Named .png but containing executable MZ header
    res_disguised = await client.post(
        f"/api/v1/threat-reports/{report_id}/evidence",
        headers={"Authorization": f"Bearer {cust_token}"},
        files={"file": ("fake_image.png", b"MZ\x90\x00\x03\x00executable", "image/png")},
    )
    assert res_disguised.status_code == 400
    assert "Executable, binary script" in res_disguised.json()["error"]["message"]

    # 3. Disguised file: Named .jpg but random plaintext without JPEG magic bytes
    res_fake_jpg = await client.post(
        f"/api/v1/threat-reports/{report_id}/evidence",
        headers={"Authorization": f"Bearer {cust_token}"},
        files={"file": ("scam.jpg", b"this is not a jpeg image at all", "image/jpeg")},
    )
    assert res_fake_jpg.status_code == 400
    assert "signature" in res_fake_jpg.json()["error"]["message"]


async def test_evidence_path_traversal_prevention(
    client: AsyncClient, mock_otp: MockOTPProvider
) -> None:
    """Verify filenames with directory traversal sequences are sanitized and isolated."""
    _, cust_token = await _create_user(client, mock_otp, "+14155557023")

    rep = await client.post(
        "/api/v1/threat-reports",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={
            "target_type": "DOMAIN",
            "target_value": "evil-domain.com",
            "description": "Domain hosting scam.",
        },
    )
    report_id = rep.json()["id"]

    # Filename trying to traverse out
    traversal_name = "../../../../etc/passwd.txt"
    valid_text_bytes = b"Sample text log showing the scam message received."

    res = await client.post(
        f"/api/v1/threat-reports/{report_id}/evidence",
        headers={"Authorization": f"Bearer {cust_token}"},
        files={"file": (traversal_name, valid_text_bytes, "text/plain")},
        data={"evidence_type": "LOG"},
    )
    assert res.status_code == 201
    saved_filename = res.json()["original_filename"]
    # Path separators must be stripped
    assert "/" not in saved_filename
    assert "\\" not in saved_filename
    assert ".." not in saved_filename
    assert saved_filename == "passwd.txt"


async def test_unauthorized_evidence_access_and_safe_download(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """
    Verify evidence access authorization:
    - User A uploads evidence.
    - User B cannot download User A's evidence (403 Forbidden).
    - Unauthenticated user cannot download (401 Unauthorized).
    - User A can download with nosniff and attachment headers.
    - Admin can download.
    """
    _, cust_a_token = await _create_user(client, mock_otp, "+14155557024")
    _, cust_b_token = await _create_user(client, mock_otp, "+14155557025")
    _, admin_token = await _create_admin(client, mock_otp, "+14155557026", db_session)

    # Customer A submits report and evidence
    rep = await client.post(
        "/api/v1/threat-reports",
        headers={"Authorization": f"Bearer {cust_a_token}"},
        json={
            "target_type": "DOMAIN",
            "target_value": "brand-impersonation.net",
            "description": "Phishing site.",
        },
    )
    report_id = rep.json()["id"]

    valid_pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    upload_res = await client.post(
        f"/api/v1/threat-reports/{report_id}/evidence",
        headers={"Authorization": f"Bearer {cust_a_token}"},
        files={"file": ("evidence_document.pdf", valid_pdf_bytes, "application/pdf")},
        data={"evidence_type": "DOCUMENT"},
    )
    evidence_id = upload_res.json()["id"]

    # 1. Unauthenticated download -> 401
    res_anon = await client.get(
        f"/api/v1/threat-reports/{report_id}/evidence/{evidence_id}"
    )
    assert res_anon.status_code == 401

    # 2. Customer B attempts download -> 403 Forbidden
    res_b = await client.get(
        f"/api/v1/threat-reports/{report_id}/evidence/{evidence_id}",
        headers={"Authorization": f"Bearer {cust_b_token}"},
    )
    assert res_b.status_code == 403
    assert res_b.json()["error"]["code"] == "ACCESS_FORBIDDEN"

    # 3. Customer A downloads -> 200 OK with security headers
    res_a = await client.get(
        f"/api/v1/threat-reports/{report_id}/evidence/{evidence_id}",
        headers={"Authorization": f"Bearer {cust_a_token}"},
    )
    assert res_a.status_code == 200
    assert res_a.headers["x-content-type-options"] == "nosniff"
    assert "attachment" in res_a.headers["content-disposition"]
    assert res_a.content == valid_pdf_bytes

    # 4. Admin downloads -> 200 OK
    res_admin = await client.get(
        f"/api/v1/threat-reports/{report_id}/evidence/{evidence_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin.status_code == 200
    assert res_admin.content == valid_pdf_bytes


async def test_evidence_file_size_limit_enforced(
    client: AsyncClient, mock_otp: MockOTPProvider, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify oversized files exceeding MAX_EVIDENCE_FILE_SIZE_BYTES are rejected with 413."""
    _, cust_token = await _create_user(client, mock_otp, "+14155557027")

    rep = await client.post(
        "/api/v1/threat-reports",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={
            "target_type": "DOMAIN",
            "target_value": "bigfile-test.com",
            "description": "Testing file size restriction.",
        },
    )
    report_id = rep.json()["id"]

    # Temporarily set max file size to 100 bytes for test
    from app.core.config import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, "MAX_EVIDENCE_FILE_SIZE_BYTES", 100)

    oversized_content = b"\x89PNG\r\n\x1a\n" + b"A" * 200  # 208 bytes > 100 bytes

    res = await client.post(
        f"/api/v1/threat-reports/{report_id}/evidence",
        headers={"Authorization": f"Bearer {cust_token}"},
        files={"file": ("large_image.png", oversized_content, "image/png")},
    )
    assert res.status_code == 413
    assert "exceeds maximum allowed size" in res.json()["error"]["message"]
