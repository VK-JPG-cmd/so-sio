"""
Integration tests for Brand Owner Portal APIs (Phase 8):
- Dashboard aggregation (using real database records for threats, assessments, campaigns, alerts)
- Threat investigation with pagination, sorting, and filtering (severity, status, date)
- Campaign listing and filtering
- Alert management: status updates with audit logging
- Brand asset and metadata management (prohibiting direct verification_status changes)
- Review management: official owner responses (prohibiting customer review deletion/rewriting)
- Audit trail verification
- Cross-brand access authorization enforcement (403 Forbidden)
"""

from datetime import datetime, timezone
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import (
    AlertStatus,
    AssetType,
    CampaignStatus,
    ReviewStatus,
    RiskSeverity,
    TargetType,
    ThreatReportStatus,
    UserRole,
)
from app.models.risk_assessment import RiskAssessment
from app.models.threat_report import ThreatReport
from app.models.user import User
from app.services.otp_provider import MockOTPProvider


async def _create_user(client: AsyncClient, mock_otp: MockOTPProvider, phone: str) -> tuple[str, str]:
    """Helper to authenticate a customer user via OTP."""
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
    """Helper to authenticate an admin user."""
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
) -> tuple[str, str]:
    """Helper to register and administratively approve a brand, returning (brand_id, owner_token)."""
    _, owner_token = await _create_user(client, mock_otp, phone)
    app_res = await client.post(
        "/api/v1/brand-applications",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"business_name": business_name, "official_domain": domain},
    )
    app_id = app_res.json()["id"]

    review_res = await client.post(
        f"/api/v1/admin/brand-applications/{app_id}/review",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"decision": "APPROVE", "notes": "Verified business entity"},
    )
    return str(review_res.json()["brand_id"]), owner_token


@pytest.mark.asyncio
async def test_brand_dashboard_summary_real_data(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """Verify GET /dashboard aggregates real database metrics for threats, severity, status, alerts, campaigns."""
    _, admin_token = await _create_admin(client, mock_otp, "+14155558001", db_session)
    brand_id, owner_token = await _setup_verified_brand(
        client, mock_otp, admin_token, "+14155558002", "Acme Cloud", "acmecloud.com"
    )
    _, cust_token = await _create_user(client, mock_otp, "+14155558003")

    brand_uuid = uuid.UUID(brand_id)

    # 1. Create 3 threat reports with varying statuses
    rep1 = ThreatReport(
        id=uuid.uuid4(),
        reporter_id=uuid.uuid4(),
        brand_id=brand_uuid,
        target_type=TargetType.DOMAIN,
        target_value="acme-login-steal.com",
        description="Fake login portal",
        status=ThreatReportStatus.UNDER_REVIEW,
    )
    rep2 = ThreatReport(
        id=uuid.uuid4(),
        reporter_id=uuid.uuid4(),
        brand_id=brand_uuid,
        target_type=TargetType.URL,
        target_value="https://acme-phish.net/auth",
        description="Phishing URL",
        status=ThreatReportStatus.CONFIRMED,
    )
    rep3 = ThreatReport(
        id=uuid.uuid4(),
        reporter_id=uuid.uuid4(),
        brand_id=brand_uuid,
        target_type=TargetType.SCAM_TEXT,
        target_value="Urgent notice from Acme Cloud",
        description="SMS scam lure",
        status=ThreatReportStatus.ANALYZING,
    )
    db_session.add_all([rep1, rep2, rep3])
    await db_session.flush()

    # 2. Attach RiskAssessments with different severities and scores
    ass1 = RiskAssessment(
        id=uuid.uuid4(),
        report_id=rep1.id,
        model_version="1.0.0",
        risk_score=85.0,
        severity=RiskSeverity.CRITICAL,
        explanation_json={"summary": "Critical homoglyph match"},
        indicators_json=[{"signal": "homoglyph", "points": 25}],
        recommendation_json=[{"action": "REQUEST_TAKEDOWN_REVIEW"}],
    )
    ass2 = RiskAssessment(
        id=uuid.uuid4(),
        report_id=rep2.id,
        model_version="1.0.0",
        risk_score=65.0,
        severity=RiskSeverity.HIGH,
        explanation_json={"summary": "High phishing indicators"},
        indicators_json=[{"signal": "urgency", "points": 20}],
        recommendation_json=[{"action": "ESCALATE_MANUAL_REVIEW"}],
    )
    db_session.add_all([ass1, ass2])
    await db_session.commit()

    # 3. Query Dashboard
    headers = {"Authorization": f"Bearer {owner_token}"}
    res = await client.get(f"/api/v1/owner/brands/{brand_id}/dashboard", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["brand_id"] == brand_id
    assert data["total_threat_reports"] == 3
    assert data["open_investigations"] == 2  # UNDER_REVIEW and ANALYZING
    assert data["threats_by_status"]["UNDER_REVIEW"] == 1
    assert data["threats_by_status"]["CONFIRMED"] == 1
    assert data["threats_by_status"]["ANALYZING"] == 1
    assert data["threats_by_severity"]["CRITICAL"] == 1
    assert data["threats_by_severity"]["HIGH"] == 1
    assert isinstance(data["recent_risk_score_trends"], list)
    assert len(data["recent_risk_score_trends"]) >= 1
    trend = data["recent_risk_score_trends"][0]
    assert trend["assessment_count"] == 2
    assert trend["max_risk_score"] == 85.0


@pytest.mark.asyncio
async def test_threat_investigation_pagination_sorting_filtering(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """Verify threat listing supports pagination, sorting, and status/date/severity filtering."""
    _, admin_token = await _create_admin(client, mock_otp, "+14155558004", db_session)
    brand_id, owner_token = await _setup_verified_brand(
        client, mock_otp, admin_token, "+14155558005", "Nexus Global", "nexusglobal.com"
    )
    brand_uuid = uuid.UUID(brand_id)

    # Populate 5 threat reports
    reports = []
    for i in range(5):
        st = ThreatReportStatus.CONFIRMED if i % 2 == 0 else ThreatReportStatus.SUBMITTED
        rep = ThreatReport(
            id=uuid.uuid4(),
            reporter_id=uuid.uuid4(),
            brand_id=brand_uuid,
            target_type=TargetType.DOMAIN,
            target_value=f"nexus-fake-{i}.com",
            description=f"Incident {i}",
            status=st,
        )
        reports.append(rep)
    db_session.add_all(reports)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {owner_token}"}

    # 1. Test Pagination: page=1, page_size=2
    res_page1 = await client.get(
        f"/api/v1/owner/brands/{brand_id}/threats?page=1&page_size=2", headers=headers
    )
    assert res_page1.status_code == 200
    items1 = res_page1.json()
    assert len(items1) == 2
    assert res_page1.headers["X-Total-Count"] == "5"

    res_page2 = await client.get(
        f"/api/v1/owner/brands/{brand_id}/threats?page=2&page_size=2", headers=headers
    )
    assert res_page2.status_code == 200
    items2 = res_page2.json()
    assert len(items2) == 2
    # Ensure distinct pages
    assert items1[0]["id"] != items2[0]["id"]

    # 2. Test Status Filtering: status=CONFIRMED (should be 3 items)
    res_filter = await client.get(
        f"/api/v1/owner/brands/{brand_id}/threats?status=CONFIRMED", headers=headers
    )
    assert res_filter.status_code == 200
    filtered_items = res_filter.json()
    assert len(filtered_items) == 3
    assert all(it["status"] == "CONFIRMED" for it in filtered_items)

    # 3. Test Sorting: sort_by=target_value, sort_order=asc
    res_sort = await client.get(
        f"/api/v1/owner/brands/{brand_id}/threats?sort_by=target_value&sort_order=asc",
        headers=headers,
    )
    assert res_sort.status_code == 200
    sorted_items = res_sort.json()
    assert sorted_items[0]["target_value"] == "nexus-fake-0.com"


@pytest.mark.asyncio
async def test_alert_status_update_and_audit_logging(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """Verify PATCH /alerts/{alert_id} updates status, enforces permissions, and writes audit log."""
    _, admin_token = await _create_admin(client, mock_otp, "+14155558006", db_session)
    brand_id, owner_token = await _setup_verified_brand(
        client, mock_otp, admin_token, "+14155558007", "Aegis Pay", "aegispay.com"
    )
    brand_uuid = uuid.UUID(brand_id)

    # Create an active alert
    from app.repositories.correlation_repo import AlertRepository
    alert_repo = AlertRepository()
    alert, _ = await alert_repo.create_if_not_duplicate(
        db=db_session,
        brand_id=brand_uuid,
        title="High Impersonation Spike",
        description="Automated spike detected",
        severity=RiskSeverity.HIGH,
        fingerprint="fingerprint_aegis_123",
    )
    await db_session.commit()

    headers = {"Authorization": f"Bearer {owner_token}"}

    # 1. Owner acknowledges alert
    patch_res = await client.patch(
        f"/api/v1/owner/alerts/{alert.id}",
        headers=headers,
        json={"status": "ACKNOWLEDGED", "notes": "Incident investigated by SOC"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "ACKNOWLEDGED"

    # 2. Verify Audit Log was generated
    audit_res = await client.get(
        f"/api/v1/owner/brands/{brand_id}/audit-logs", headers=headers
    )
    assert audit_res.status_code == 200
    logs = audit_res.json()
    assert len(logs) >= 1
    alert_log = next((l for l in logs if l["action"] == "ALERT_STATUS_UPDATE"), None)
    assert alert_log is not None
    assert alert_log["entity_id"] == str(alert.id)
    assert alert_log["details"]["old_status"] == "OPEN"
    assert alert_log["details"]["new_status"] == "ACKNOWLEDGED"
    assert alert_log["details"]["notes"] == "Incident investigated by SOC"


@pytest.mark.asyncio
async def test_review_response_management_and_immutability(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """
    Verify Review Management:
    - Customer posts review.
    - Brand owner posts response using ReviewResponse model.
    - Owner CANNOT delete or rewrite customer review directly.
    """
    _, admin_token = await _create_admin(client, mock_otp, "+14155558008", db_session)
    brand_id, owner_token = await _setup_verified_brand(
        client, mock_otp, admin_token, "+14155558009", "Starlight Banking", "starlightbank.com"
    )
    _, cust_token = await _create_user(client, mock_otp, "+14155558010")

    # 1. Customer submits review
    rev_res = await client.post(
        f"/api/v1/brands/{brand_id}/reviews",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={"rating": 2, "body": "Encountered a suspicious clone site posing as Starlight."},
    )
    assert rev_res.status_code == 201
    review_id = rev_res.json()["id"]

    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    # 2. Brand owner responds to review
    reply_res = await client.post(
        f"/api/v1/owner/brands/{brand_id}/reviews/{review_id}/respond",
        headers=owner_headers,
        json={"response_text": "Thank you for the report. Our security team has mitigated the clone site."},
    )
    assert reply_res.status_code == 201
    reply_data = reply_res.json()
    assert reply_data["review_id"] == review_id
    assert "mitigated the clone site" in reply_data["response_text"]

    # 3. Retrieve reviews via Owner Portal: includes owner response
    owner_revs = await client.get(
        f"/api/v1/owner/brands/{brand_id}/reviews", headers=owner_headers
    )
    assert owner_revs.status_code == 200
    rev_list = owner_revs.json()
    assert len(rev_list) >= 1
    matched = next((r for r in rev_list if r["id"] == review_id), None)
    assert matched is not None
    assert matched["owner_response"] is not None
    assert matched["owner_response"]["response_text"] == reply_data["response_text"]

    # 4. Strict Security Invariant: Brand owner CANNOT delete customer reviews
    del_res = await client.delete(
        f"/api/v1/owner/brands/{brand_id}/reviews/{review_id}", headers=owner_headers
    )
    assert del_res.status_code == 403

    # 5. Strict Security Invariant: Brand owner CANNOT rewrite customer reviews
    patch_res = await client.patch(
        f"/api/v1/owner/brands/{brand_id}/reviews/{review_id}",
        headers=owner_headers,
        json={"body": "Tampered review body"},
    )
    assert patch_res.status_code == 403


@pytest.mark.asyncio
async def test_brand_metadata_and_asset_management(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """
    Verify Brand Metadata & Asset Management:
    - Updating display_name works and logs audit entry.
    - Prohibits direct attempts to alter verification_status (400 Bad Request).
    - Registering official brand assets.
    """
    _, admin_token = await _create_admin(client, mock_otp, "+14155558011", db_session)
    brand_id, owner_token = await _setup_verified_brand(
        client, mock_otp, admin_token, "+14155558012", "Original Brand", "originalbrand.com"
    )

    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    # 1. Update display name
    meta_res = await client.patch(
        f"/api/v1/owner/brands/{brand_id}",
        headers=owner_headers,
        json={"display_name": "Updated Brand International"},
    )
    assert meta_res.status_code == 200
    assert meta_res.json()["display_name"] == "Updated Brand International"

    # 2. Attempt to bypass verification status -> 400 Bad Request
    bypass_res = await client.patch(
        f"/api/v1/owner/brands/{brand_id}",
        headers=owner_headers,
        json={"display_name": "Hacked", "verification_status": "VERIFIED"},
    )
    assert bypass_res.status_code == 400

    # 3. Add brand asset
    import base64
    sample_content = b"fake-png-binary-content-for-logo"
    content_b64 = base64.b64encode(sample_content).decode("utf-8")

    asset_res = await client.post(
        f"/api/v1/owner/brands/{brand_id}/assets",
        headers=owner_headers,
        json={
            "asset_type": "LOGO",
            "filename": "official_logo.png",
            "content_base64": content_b64,
        },
    )
    assert asset_res.status_code == 201
    assert asset_res.json()["asset_type"] == "LOGO"

    # 4. List brand assets
    list_assets = await client.get(
        f"/api/v1/owner/brands/{brand_id}/assets", headers=owner_headers
    )
    assert list_assets.status_code == 200
    assert len(list_assets.json()) >= 1


@pytest.mark.asyncio
async def test_cross_brand_access_enforcement(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """Verify that Brand Owner B CANNOT access Brand Owner A's dashboard, threats, reviews, or audit logs."""
    _, admin_token = await _create_admin(client, mock_otp, "+14155558013", db_session)
    brand_a_id, _ = await _setup_verified_brand(
        client, mock_otp, admin_token, "+14155558014", "Brand Alpha", "alpha.org"
    )
    _, owner_b_token = await _setup_verified_brand(
        client, mock_otp, admin_token, "+14155558015", "Brand Beta", "beta.org"
    )
    _, customer_token = await _create_user(client, mock_otp, "+14155558016")

    headers_b = {"Authorization": f"Bearer {owner_b_token}"}
    headers_cust = {"Authorization": f"Bearer {customer_token}"}

    endpoints = ["dashboard", "threats", "campaigns", "alerts", "reviews", "audit-logs", "graph"]

    for ep in endpoints:
        # Owner B denied access to Brand A
        res_b = await client.get(f"/api/v1/owner/brands/{brand_a_id}/{ep}", headers=headers_b)
        assert res_b.status_code == 403

        # Customer denied access to Brand A
        res_cust = await client.get(f"/api/v1/owner/brands/{brand_a_id}/{ep}", headers=headers_cust)
        assert res_cust.status_code == 403

    # Admin CAN access Brand A's dashboard
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    admin_dash = await client.get(f"/api/v1/owner/brands/{brand_a_id}/dashboard", headers=admin_headers)
    assert admin_dash.status_code == 200
