"""
Integration test suite for Phase 9: Customer Portal APIs.

Verifies:
1. Verified brand discovery (search, pagination, filtering by verification status)
2. Brand detail with safe public metadata and approved published reviews
3. Customer review submission with rating and text length validation
4. Customer review history with pagination and status filtering
5. Threat report submission with URL and domain validation
6. Customer threat report history with pagination and status filtering
7. Threat report details and status
8. Secure evidence upload and attachment download handling
9. Input validation across bounds, lengths, file types, and sizes
10. Strict privacy isolation: cross-user report and evidence access forbidden (403),
    no PII or internal investigation notes leaked on public endpoints.
"""

import io
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ReviewStatus, ThreatReportStatus, UserRole
from app.models.user import User
from app.services.otp_provider import MockOTPProvider


async def _create_user(
    client: AsyncClient, mock_otp: MockOTPProvider, phone: str
) -> tuple[str, str]:
    """Helper to authenticate a customer user via OTP and return (user_id, access_token)."""
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
    phone: str,
    business_name: str,
    domain: str,
) -> str:
    """Helper to register and administratively approve a brand, returning its brand_id."""
    _, owner_token = await _create_user(client, mock_otp, phone)
    app_res = await client.post(
        "/api/v1/brand-applications",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"business_name": business_name, "official_domain": domain},
    )
    assert app_res.status_code == 201
    app_id = app_res.json()["id"]

    review_res = await client.post(
        f"/api/v1/admin/brand-applications/{app_id}/review",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"decision": "APPROVE"},
    )
    assert review_res.status_code == 200
    brand_id = review_res.json().get("brand_id")
    if brand_id:
        return brand_id
    brand_res = await client.get("/api/v1/brands")
    for b in brand_res.json():
        if b["official_domain"] == domain:
            return b["id"]
    raise RuntimeError(f"Brand with domain {domain} was not found after approval")


@pytest.mark.asyncio
async def test_verified_brand_discovery_search_and_pagination(
    client: AsyncClient,
    mock_otp: MockOTPProvider,
    db_session: AsyncSession,
):
    """
    Test GET /api/v1/brands:
    - Search by keyword (display_name or official_domain)
    - Pagination (page, page_size, limit, offset, and headers X-Total-Count, X-Page, X-Page-Size)
    - Filtering by verification_status
    """
    _, admin_token = await _create_admin(client, mock_otp, "+14155558100", db_session)

    b1_id = await _setup_verified_brand(
        client, mock_otp, admin_token, "+14155558101", "Acme Corp", "acme-corp.com"
    )
    b2_id = await _setup_verified_brand(
        client, mock_otp, admin_token, "+14155558102", "Apex Bank", "apexbank.org"
    )
    b3_id = await _setup_verified_brand(
        client, mock_otp, admin_token, "+14155558103", "Apex Cloud", "apexcloud.io"
    )

    # 1. Search by name keyword
    search_res = await client.get("/api/v1/brands?search=apex")
    assert search_res.status_code == 200
    search_items = search_res.json()
    assert len(search_items) == 2
    domains = {b["official_domain"] for b in search_items}
    assert "apexbank.org" in domains
    assert "apexcloud.io" in domains

    # 2. Search by domain substring
    domain_res = await client.get("/api/v1/brands?search=acme-corp")
    assert domain_res.status_code == 200
    domain_items = domain_res.json()
    assert len(domain_items) == 1
    assert domain_items[0]["display_name"] == "Acme Corp"

    # 3. Search with no matches
    empty_res = await client.get("/api/v1/brands?search=nonexistent-query-999")
    assert empty_res.status_code == 200
    assert empty_res.json() == []
    assert empty_res.headers.get("X-Total-Count") == "0"

    # 4. Pagination (page 1, page_size 2)
    p1_res = await client.get("/api/v1/brands?page=1&page_size=2")
    assert p1_res.status_code == 200
    p1_items = p1_res.json()
    assert len(p1_items) == 2
    assert int(p1_res.headers["X-Total-Count"]) >= 3
    assert p1_res.headers["X-Page"] == "1"
    assert p1_res.headers["X-Page-Size"] == "2"

    # 5. Pagination (page 2, page_size 2)
    p2_res = await client.get("/api/v1/brands?page=2&page_size=2")
    assert p2_res.status_code == 200
    p2_items = p2_res.json()
    assert len(p2_items) >= 1
    assert p2_res.headers["X-Page"] == "2"

    # Ensure items on page 1 and page 2 do not overlap
    p1_ids = {x["id"] for x in p1_items}
    p2_ids = {x["id"] for x in p2_items}
    assert p1_ids.isdisjoint(p2_ids)

    # 6. Status filter
    status_res = await client.get("/api/v1/brands?verification_status=VERIFIED")
    assert status_res.status_code == 200
    for b in status_res.json():
        assert b["verification_status"] == "VERIFIED"


@pytest.mark.asyncio
async def test_brand_detail_safe_info_and_published_reviews(
    client: AsyncClient,
    mock_otp: MockOTPProvider,
    db_session: AsyncSession,
):
    """
    Test GET /api/v1/brands/{brand_id}:
    - Returns safe public information
    - Returns only approved published reviews (omits pending and rejected reviews)
    """
    _, admin_token = await _create_admin(client, mock_otp, "+14155558200", db_session)
    brand_id = await _setup_verified_brand(
        client, mock_otp, admin_token, "+14155558201", "Vanguard Security", "vanguardsec.com"
    )

    _, cust1_token = await _create_user(client, mock_otp, "+14155558210")
    _, cust2_token = await _create_user(client, mock_otp, "+14155558220")

    # Brand initially has no published reviews
    detail_res = await client.get(f"/api/v1/brands/{brand_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["display_name"] == "Vanguard Security"
    assert detail_data["official_domain"] == "vanguardsec.com"
    assert detail_data["published_reviews"] == []

    # Cust1 submits a review (starts as PENDING_MODERATION)
    rev1_res = await client.post(
        f"/api/v1/brands/{brand_id}/reviews",
        headers={"Authorization": f"Bearer {cust1_token}"},
        json={"rating": 5, "body": "Excellent security service, protected our team completely!"},
    )
    assert rev1_res.status_code == 201
    rev1_id = rev1_res.json()["id"]

    # Pending review must NOT be visible on public brand detail
    detail_res_pending = await client.get(f"/api/v1/brands/{brand_id}")
    assert detail_res_pending.status_code == 200
    assert len(detail_res_pending.json()["published_reviews"]) == 0

    # Cust2 submits another review (which gets rejected by admin)
    rev2_res = await client.post(
        f"/api/v1/brands/{brand_id}/reviews",
        headers={"Authorization": f"Bearer {cust2_token}"},
        json={"rating": 1, "body": "Spam test review with abusive text not suitable for site."},
    )
    assert rev2_res.status_code == 201
    rev2_id = rev2_res.json()["id"]

    # Admin publishes rev1 and rejects rev2
    await client.patch(
        f"/api/v1/reviews/{rev1_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "PUBLISHED"},
    )
    await client.patch(
        f"/api/v1/reviews/{rev2_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "REJECTED"},
    )

    # Now public brand detail must show only the published review
    detail_res_published = await client.get(f"/api/v1/brands/{brand_id}")
    assert detail_res_published.status_code == 200
    pub_reviews = detail_res_published.json()["published_reviews"]
    assert len(pub_reviews) == 1
    assert pub_reviews[0]["id"] == rev1_id
    assert pub_reviews[0]["rating"] == 5
    assert "protected our team" in pub_reviews[0]["body"]


@pytest.mark.asyncio
async def test_customer_review_input_validation(
    client: AsyncClient,
    mock_otp: MockOTPProvider,
    db_session: AsyncSession,
):
    """
    Test review submission bounds:
    - Rating bounds (1 to 5)
    - Body length bounds (10 to 5000 chars)
    """
    _, admin_token = await _create_admin(client, mock_otp, "+14155558300", db_session)
    brand_id = await _setup_verified_brand(
        client, mock_otp, admin_token, "+14155558301", "Shield Tech", "shieldtech.net"
    )
    _, cust_token = await _create_user(client, mock_otp, "+14155558310")

    # Invalid rating (0)
    res_zero = await client.post(
        f"/api/v1/brands/{brand_id}/reviews",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={"rating": 0, "body": "A valid length review body text."},
    )
    assert res_zero.status_code == 422

    # Invalid rating (6)
    res_six = await client.post(
        f"/api/v1/brands/{brand_id}/reviews",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={"rating": 6, "body": "A valid length review body text."},
    )
    assert res_six.status_code == 422

    # Body too short (< 10 chars)
    res_short = await client.post(
        f"/api/v1/brands/{brand_id}/reviews",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={"rating": 5, "body": "Too short"},
    )
    assert res_short.status_code == 422

    # Body too long (> 5000 chars)
    res_long = await client.post(
        f"/api/v1/brands/{brand_id}/reviews",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={"rating": 5, "body": "x" * 5001},
    )
    assert res_long.status_code == 422


@pytest.mark.asyncio
async def test_customer_review_history_and_pagination(
    client: AsyncClient,
    mock_otp: MockOTPProvider,
    db_session: AsyncSession,
):
    """
    Test GET /api/v1/users/me/reviews:
    - Returns all reviews submitted by the authenticated customer
    - Supports pagination (page, page_size) and headers (X-Total-Count, X-Page, X-Page-Size)
    - Supports status filtering
    - Isolates history from other customers
    """
    _, admin_token = await _create_admin(client, mock_otp, "+14155558400", db_session)
    brand_id = await _setup_verified_brand(
        client, mock_otp, admin_token, "+14155558401", "Secure Fin", "securefin.io"
    )

    _, cust1_token = await _create_user(client, mock_otp, "+14155558410")
    _, cust2_token = await _create_user(client, mock_otp, "+14155558420")

    # Customer 1 posts 3 reviews
    r1 = await client.post(
        f"/api/v1/brands/{brand_id}/reviews",
        headers={"Authorization": f"Bearer {cust1_token}"},
        json={"rating": 5, "body": "Review one with detailed customer experience remarks."},
    )
    r2 = await client.post(
        f"/api/v1/brands/{brand_id}/reviews",
        headers={"Authorization": f"Bearer {cust1_token}"},
        json={"rating": 4, "body": "Review two with helpful comments about usability and speed."},
    )
    r3 = await client.post(
        f"/api/v1/brands/{brand_id}/reviews",
        headers={"Authorization": f"Bearer {cust1_token}"},
        json={"rating": 3, "body": "Review three with average experience and constructive input."},
    )
    assert r1.status_code == 201 and r2.status_code == 201 and r3.status_code == 201
    r1_id = r1.json()["id"]

    # Admin publishes r1
    await client.patch(
        f"/api/v1/reviews/{r1_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "PUBLISHED"},
    )

    # Cust1 gets all their reviews with pagination
    history_res = await client.get(
        "/api/v1/users/me/reviews?page=1&page_size=2",
        headers={"Authorization": f"Bearer {cust1_token}"},
    )
    assert history_res.status_code == 200
    assert len(history_res.json()) == 2
    assert history_res.headers["X-Total-Count"] == "3"
    assert history_res.headers["X-Page"] == "1"
    assert history_res.headers["X-Page-Size"] == "2"

    # Cust1 filters by status
    pub_res = await client.get(
        "/api/v1/users/me/reviews?status=PUBLISHED",
        headers={"Authorization": f"Bearer {cust1_token}"},
    )
    assert pub_res.status_code == 200
    assert len(pub_res.json()) == 1
    assert pub_res.json()[0]["id"] == r1_id
    assert pub_res.headers["X-Total-Count"] == "1"

    pending_res = await client.get(
        "/api/v1/users/me/reviews?status=PENDING_MODERATION",
        headers={"Authorization": f"Bearer {cust1_token}"},
    )
    assert pending_res.status_code == 200
    assert len(pending_res.json()) == 2
    assert pending_res.headers["X-Total-Count"] == "2"

    # Cust2 has no reviews yet
    cust2_res = await client.get(
        "/api/v1/users/me/reviews",
        headers={"Authorization": f"Bearer {cust2_token}"},
    )
    assert cust2_res.status_code == 200
    assert cust2_res.json() == []
    assert cust2_res.headers["X-Total-Count"] == "0"


@pytest.mark.asyncio
async def test_threat_report_submission_and_input_validation(
    client: AsyncClient,
    mock_otp: MockOTPProvider,
    db_session: AsyncSession,
):
    """
    Test threat report submission:
    - DOMAIN normalization
    - URL scheme and host validation
    - Description length bounds
    """
    _, cust_token = await _create_user(client, mock_otp, "+14155558510")

    # 1. Valid DOMAIN submission
    res_domain = await client.post(
        "/api/v1/threat-reports",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={
            "target_type": "DOMAIN",
            "target_value": "  FAKE-BRAND.COM  ",
            "description": "Suspected impersonation domain targeting customer login portal.",
        },
    )
    assert res_domain.status_code == 201
    assert res_domain.json()["target_value"] == "fake-brand.com"
    assert res_domain.json()["status"] == "SUBMITTED"

    # 2. Valid URL submission
    res_url = await client.post(
        "/api/v1/threat-reports",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={
            "target_type": "URL",
            "target_value": "https://malicious-phish.net/login/verify?token=123",
            "description": "Phishing landing page asking for credit card and credentials.",
        },
    )
    assert res_url.status_code == 201
    assert "https://malicious-phish.net" in res_url.json()["target_value"]

    # 3. Invalid URL target (missing scheme or invalid protocol)
    res_bad_url = await client.post(
        "/api/v1/threat-reports",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={
            "target_type": "URL",
            "target_value": "ftp://malicious-phish.net/file.iso",
            "description": "Invalid protocol for a URL threat report submission.",
        },
    )
    assert res_bad_url.status_code == 422

    # 4. Description too short (< 10 chars)
    res_short = await client.post(
        "/api/v1/threat-reports",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={
            "target_type": "DOMAIN",
            "target_value": "suspicious-site.org",
            "description": "Too brief",
        },
    )
    assert res_short.status_code == 422


@pytest.mark.asyncio
async def test_customer_threat_report_history_and_details(
    client: AsyncClient,
    mock_otp: MockOTPProvider,
    db_session: AsyncSession,
):
    """
    Test GET /api/v1/users/me/threat-reports and GET /api/v1/threat-reports/{report_id}:
    - User report history with pagination and status filtering
    - Report details and status retrieval
    """
    _, cust_token = await _create_user(client, mock_otp, "+14155558610")

    rep1 = await client.post(
        "/api/v1/threat-reports",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={
            "target_type": "DOMAIN",
            "target_value": "first-threat.org",
            "description": "First suspicious threat report submitted by user.",
        },
    )
    rep2 = await client.post(
        "/api/v1/threat-reports",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={
            "target_type": "URL",
            "target_value": "https://second-threat.net/claim",
            "description": "Second suspicious threat report submitted by user.",
        },
    )
    assert rep1.status_code == 201 and rep2.status_code == 201
    rep1_id = rep1.json()["id"]

    # History list with pagination
    history_res = await client.get(
        "/api/v1/users/me/threat-reports?page=1&page_size=10",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert history_res.status_code == 200
    assert len(history_res.json()) == 2
    assert history_res.headers["X-Total-Count"] == "2"
    assert history_res.headers["X-Page"] == "1"

    # Status filter
    filter_res = await client.get(
        "/api/v1/users/me/threat-reports?status=SUBMITTED",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert filter_res.status_code == 200
    assert len(filter_res.json()) == 2

    # Query details endpoint
    detail_res = await client.get(
        f"/api/v1/threat-reports/{rep1_id}",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == rep1_id
    assert detail_res.json()["target_value"] == "first-threat.org"
    assert detail_res.json()["status"] == "SUBMITTED"


@pytest.mark.asyncio
async def test_evidence_attachment_and_privacy_boundaries(
    client: AsyncClient,
    mock_otp: MockOTPProvider,
    db_session: AsyncSession,
):
    """
    Test evidence upload and access control:
    - User A uploads PNG evidence to their report -> 201 Created
    - User A downloads evidence -> 200 OK with security headers
    - User B attempts to download User A's evidence -> 403 Forbidden
    - User B attempts to upload evidence to User A's report -> 403 Forbidden
    - User B attempts to view User A's threat report details -> 403 Forbidden
    - Disallowed file type / executable is rejected -> 400 Bad Request
    """
    _, cust_a_token = await _create_user(client, mock_otp, "+14155558710")
    _, cust_b_token = await _create_user(client, mock_otp, "+14155558720")

    # Customer A creates report
    rep = await client.post(
        "/api/v1/threat-reports",
        headers={"Authorization": f"Bearer {cust_a_token}"},
        json={
            "target_type": "URL",
            "target_value": "https://phish-login-bank.com/auth",
            "description": "Phishing portal masquerading as real login screen.",
        },
    )
    assert rep.status_code == 201
    rep_id = rep.json()["id"]

    # 1. Customer A uploads valid PNG screenshot
    # Valid 1x1 PNG binary bytes
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05"
        b"\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    files = {"file": ("screenshot.png", io.BytesIO(png_bytes), "image/png")}
    upload_res = await client.post(
        f"/api/v1/threat-reports/{rep_id}/evidence",
        headers={"Authorization": f"Bearer {cust_a_token}"},
        files=files,
        data={"evidence_type": "SCREENSHOT"},
    )
    assert upload_res.status_code == 201
    evidence_id = upload_res.json()["id"]

    # 2. Customer A successfully downloads evidence
    download_res = await client.get(
        f"/api/v1/threat-reports/{rep_id}/evidence/{evidence_id}",
        headers={"Authorization": f"Bearer {cust_a_token}"},
    )
    assert download_res.status_code == 200
    assert download_res.headers.get("X-Content-Type-Options") == "nosniff"
    assert "private" in download_res.headers.get("Cache-Control", "")

    # 3. Privacy Boundary: Customer B tries to download Customer A's evidence -> 403 Forbidden
    cross_download = await client.get(
        f"/api/v1/threat-reports/{rep_id}/evidence/{evidence_id}",
        headers={"Authorization": f"Bearer {cust_b_token}"},
    )
    assert cross_download.status_code == 403

    # 4. Privacy Boundary: Customer B tries to upload evidence to Customer A's report -> 403 Forbidden
    cross_upload = await client.post(
        f"/api/v1/threat-reports/{rep_id}/evidence",
        headers={"Authorization": f"Bearer {cust_b_token}"},
        files={"file": ("fake.png", io.BytesIO(png_bytes), "image/png")},
        data={"evidence_type": "SCREENSHOT"},
    )
    assert cross_upload.status_code == 403

    # 5. Privacy Boundary: Customer B tries to view Customer A's report details -> 403 Forbidden
    cross_report = await client.get(
        f"/api/v1/threat-reports/{rep_id}",
        headers={"Authorization": f"Bearer {cust_b_token}"},
    )
    assert cross_report.status_code == 403

    # 6. File security: disallowed executable file upload -> 400 Bad Request
    exe_bytes = b"MZ\x90\x00\x03\x00\x00\x00"
    bad_upload = await client.post(
        f"/api/v1/threat-reports/{rep_id}/evidence",
        headers={"Authorization": f"Bearer {cust_a_token}"},
        files={"file": ("malware.exe", io.BytesIO(exe_bytes), "application/x-msdownload")},
        data={"evidence_type": "SCREENSHOT"},
    )
    assert bad_upload.status_code == 400


@pytest.mark.asyncio
async def test_public_endpoints_never_expose_pii_or_internal_notes(
    client: AsyncClient,
    mock_otp: MockOTPProvider,
    db_session: AsyncSession,
):
    """
    Test privacy requirement:
    Public endpoints must NOT expose phone numbers or internal investigation notes:
    - GET /api/v1/brands
    - GET /api/v1/brands/{brand_id}
    - GET /api/v1/brands/{brand_id}/reviews
    """
    _, admin_token = await _create_admin(client, mock_otp, "+14155558800", db_session)
    brand_id = await _setup_verified_brand(
        client, mock_otp, admin_token, "+14155558801", "Privacy First Corp", "privacyfirst.org"
    )

    _, cust_token = await _create_user(client, mock_otp, "+14155558810")
    rev = await client.post(
        f"/api/v1/brands/{brand_id}/reviews",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={"rating": 5, "body": "Great privacy practices and outstanding support team."},
    )
    rev_id = rev.json()["id"]

    # Admin publishes review
    await client.patch(
        f"/api/v1/reviews/{rev_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "PUBLISHED"},
    )

    # 1. Inspect GET /api/v1/brands
    brands_res = await client.get("/api/v1/brands")
    assert brands_res.status_code == 200
    brands_text = brands_res.text
    assert "+14155558801" not in brands_text
    assert "+14155558810" not in brands_text
    assert "phone" not in brands_text.lower()
    assert "investigation" not in brands_text.lower()

    # 2. Inspect GET /api/v1/brands/{brand_id}
    detail_res = await client.get(f"/api/v1/brands/{brand_id}")
    assert detail_res.status_code == 200
    detail_text = detail_res.text
    assert "+14155558801" not in detail_text
    assert "+14155558810" not in detail_text
    assert "phone" not in detail_text.lower()
    assert "investigation" not in detail_text.lower()

    # 3. Inspect GET /api/v1/brands/{brand_id}/reviews
    reviews_res = await client.get(f"/api/v1/brands/{brand_id}/reviews")
    assert reviews_res.status_code == 200
    reviews_text = reviews_res.text
    assert "+14155558801" not in reviews_text
    assert "+14155558810" not in reviews_text
    assert "phone" not in reviews_text.lower()
    assert "investigation" not in reviews_text.lower()
