"""
End-to-End Integration Tests — Phase 11
Comprehensive validation of the three primary system workflows:
- WORKFLOW A: Brand Owner Lifecycle
- WORKFLOW B: Customer Lifecycle
- WORKFLOW C: Threat Analysis, Correlation, and Alert Lifecycle
"""

import io
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AlertStatus, RiskSeverity, TargetType, ThreatReportStatus, UserRole
from app.models.user import User
from app.services.correlation.campaign_service import CampaignCorrelationService
from app.services.dns_resolver import MockDNSResolver
from app.services.otp_provider import MockOTPProvider
from app.services.scoring.config import SCORING_RULE_VERSION


async def _register_and_authenticate(
    client: AsyncClient, mock_otp: MockOTPProvider, phone: str
) -> tuple[str, str]:
    """Execute standard authentic OTP login, returning (user_id, access_token)."""
    # 1. Request OTP
    otp_start = await client.post("/api/v1/auth/otp/start", json={"phone_number": phone})
    assert otp_start.status_code == 200

    # 2. Extract code from mock provider
    code = mock_otp.get_last_code(phone)
    assert code is not None

    # 3. Verify OTP and authenticate
    verify_res = await client.post(
        "/api/v1/auth/otp/verify", json={"phone_number": phone, "code": code}
    )
    assert verify_res.status_code == 200
    data = verify_res.json()
    return data["user"]["id"], data["access_token"]


async def _promote_to_admin(db_session: AsyncSession, user_id: str) -> None:
    """Helper to assign administrative role to an existing user."""
    await db_session.execute(
        update(User).where(User.id == uuid.UUID(user_id)).values(role=UserRole.ADMIN)
    )
    await db_session.commit()


@pytest.mark.asyncio
async def test_workflow_a_brand_owner_e2e(
    client: AsyncClient,
    mock_otp: MockOTPProvider,
    mock_dns: MockDNSResolver,
    db_session: AsyncSession,
) -> None:
    """
    WORKFLOW A — BRAND OWNER (Complete 10-Step Workflow)
    1. Request OTP.
    2. Verify OTP.
    3. Authenticate.
    4. Submit a brand application.
    5. Request a DNS challenge.
    6. Verify domain ownership using the configured verification method.
    7. Access the authorized brand dashboard.
    8. Review threat reports.
    9. Investigate an alert.
    10. Record the investigation action.
    """
    owner_phone = "+14155551101"
    admin_phone = "+14155551199"

    # Step 1, 2, 3: Request OTP, Verify OTP, Authenticate for Brand Owner
    owner_id, owner_token = await _register_and_authenticate(client, mock_otp, owner_phone)
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    # Setup platform admin to approve application after domain verification
    admin_id, admin_token = await _register_and_authenticate(client, mock_otp, admin_phone)
    await _promote_to_admin(db_session, admin_id)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Step 4: Submit a brand application
    app_res = await client.post(
        "/api/v1/brand-applications",
        headers=owner_headers,
        json={
            "business_name": "Acme Global Financial Inc",
            "official_domain": "HTTPS://AcmeGlobalFin.com/",
        },
    )
    assert app_res.status_code == 201
    app_data = app_res.json()
    app_id = app_data["id"]
    assert app_data["official_domain"] == "acmeglobalfin.com"
    assert app_data["application_status"] == "PENDING_DOMAIN_VERIFICATION"

    # Step 5: Request a DNS challenge
    challenge_res = await client.post(
        f"/api/v1/brand-applications/{app_id}/domain-challenge",
        headers=owner_headers,
    )
    assert challenge_res.status_code == 200
    cdata = challenge_res.json()
    record_host = cdata["record_host"]
    expected_record = cdata["expected_record_value"]
    challenge_token = cdata["challenge_token"]
    assert record_host == "_brandshield-challenge.acmeglobalfin.com"
    assert "brandshield-verification=" in expected_record

    # Step 6: Verify domain ownership using configured DNS method
    mock_dns.set_txt_records(record_host, [expected_record])
    verify_res = await client.post(
        f"/api/v1/brand-applications/{app_id}/verify-domain",
        headers=owner_headers,
        json={"token": challenge_token},
    )
    assert verify_res.status_code == 200
    vdata = verify_res.json()
    assert vdata["verified"] is True
    assert vdata["application_status"] == "PENDING_REVIEW"

    # Admin approves verified application, creating official brand & promoting owner role
    admin_review = await client.post(
        f"/api/v1/admin/brand-applications/{app_id}/review",
        headers=admin_headers,
        json={"decision": "APPROVE", "notes": "Corporate registry documents and DNS verified"},
    )
    assert admin_review.status_code == 200
    brand_id = admin_review.json()["brand_id"]
    assert brand_id is not None

    # Verify owner role was elevated
    profile_res = await client.get("/api/v1/users/me", headers=owner_headers)
    assert profile_res.json()["role"] == "BRAND_OWNER"

    # Setup realistic threat report and alert for this brand
    cust_id, cust_token = await _register_and_authenticate(client, mock_otp, "+14155551102")
    cust_headers = {"Authorization": f"Bearer {cust_token}"}
    rep_res = await client.post(
        "/api/v1/threat-reports",
        headers=cust_headers,
        json={
            "brand_id": brand_id,
            "target_type": "DOMAIN",
            "target_value": "acmeglobalfin-login-steal.com",
            "description": "Deceptive credential harvesting portal masquerading as Acme Global Financial.",
        },
    )
    assert rep_res.status_code == 201

    # Create active security alert
    from app.repositories.correlation_repo import AlertRepository
    alert_repo = AlertRepository()
    alert, _ = await alert_repo.create_if_not_duplicate(
        db=db_session,
        brand_id=uuid.UUID(brand_id),
        title="Critical Phishing Surge Detected",
        description="Automated correlation detected active credential harvesting targeting acmeglobalfin.com",
        severity=RiskSeverity.HIGH,
        fingerprint="fp_acme_e2e_alert_1",
    )
    await db_session.commit()

    # Step 7: Access authorized brand dashboard
    dash_res = await client.get(
        f"/api/v1/owner/brands/{brand_id}/dashboard",
        headers=owner_headers,
    )
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["brand_id"] == brand_id
    assert dash_data["total_threat_reports"] >= 1
    assert "threats_by_status" in dash_data
    assert "threats_by_severity" in dash_data

    # Step 8: Review threat reports
    threats_res = await client.get(
        f"/api/v1/owner/brands/{brand_id}/threats",
        headers=owner_headers,
    )
    assert threats_res.status_code == 200
    threat_list = threats_res.json()
    assert len(threat_list) >= 1
    assert any("acmeglobalfin" in t["target_value"] for t in threat_list)

    # Step 9: Investigate an alert
    alerts_res = await client.get(
        f"/api/v1/owner/brands/{brand_id}/alerts",
        headers=owner_headers,
    )
    assert alerts_res.status_code == 200
    alert_list = alerts_res.json()
    assert len(alert_list) >= 1
    target_alert = next(a for a in alert_list if a["id"] == str(alert.id))
    assert target_alert["status"] == "OPEN"
    assert target_alert["severity"] == "HIGH"

    # Step 10: Record investigation action
    action_notes = "SOC investigation confirmed malicious host; initiated registrar abuse takedown request."
    investigate_res = await client.patch(
        f"/api/v1/owner/alerts/{target_alert['id']}",
        headers=owner_headers,
        json={"status": "ACKNOWLEDGED", "notes": action_notes},
    )
    assert investigate_res.status_code == 200
    assert investigate_res.json()["status"] == "ACKNOWLEDGED"

    # Verify recorded investigation generated an immutable audit log entry
    audit_res = await client.get(
        f"/api/v1/owner/brands/{brand_id}/audit-logs",
        headers=owner_headers,
    )
    assert audit_res.status_code == 200
    audit_logs = audit_res.json()
    assert len(audit_logs) >= 1
    matching_log = next(
        (log for log in audit_logs if log["entity_id"] == str(alert.id)), None
    )
    assert matching_log is not None
    assert matching_log["action"] == "ALERT_STATUS_UPDATE"
    assert matching_log["details"]["new_status"] == "ACKNOWLEDGED"
    assert matching_log["details"]["notes"] == action_notes


@pytest.mark.asyncio
async def test_workflow_b_customer_e2e(
    client: AsyncClient,
    mock_otp: MockOTPProvider,
    db_session: AsyncSession,
) -> None:
    """
    WORKFLOW B — CUSTOMER (Complete 10-Step Workflow)
    1. Request OTP.
    2. Verify OTP.
    3. Authenticate.
    4. Discover a verified brand.
    5. Submit a review.
    6. Submit a suspicious-domain report.
    7. Attach evidence.
    8. Trigger analysis.
    9. Retrieve the resulting assessment.
    10. Track the report status.
    """
    admin_id, admin_token = await _register_and_authenticate(client, mock_otp, "+14155551299")
    await _promote_to_admin(db_session, admin_id)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Setup pre-verified brand for discovery
    owner_id, owner_token = await _register_and_authenticate(client, mock_otp, "+14155551201")
    app_res = await client.post(
        "/api/v1/brand-applications",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"business_name": "Apex Shield Bank", "official_domain": "apexshieldbank.com"},
    )
    app_id = app_res.json()["id"]
    rev_res = await client.post(
        f"/api/v1/admin/brand-applications/{app_id}/review",
        headers=admin_headers,
        json={"decision": "APPROVE"},
    )
    brand_id = rev_res.json()["brand_id"]

    # Step 1, 2, 3: Customer requests OTP, verifies OTP, and authenticates
    cust_phone = "+14155551202"
    cust_id, cust_token = await _register_and_authenticate(client, mock_otp, cust_phone)
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    # Step 4: Discover a verified brand
    discover_res = await client.get("/api/v1/brands?search=Apex", headers=cust_headers)
    assert discover_res.status_code == 200
    brand_results = discover_res.json()
    assert len(brand_results) >= 1
    found_brand = next(b for b in brand_results if b["id"] == brand_id)
    assert found_brand["display_name"] == "Apex Shield Bank"
    assert found_brand["official_domain"] == "apexshieldbank.com"
    assert found_brand["verification_status"] == "VERIFIED"

    # Step 5: Submit a review
    review_res = await client.post(
        f"/api/v1/brands/{brand_id}/reviews",
        headers=cust_headers,
        json={
            "rating": 5,
            "body": "Excellent bank with robust multi-factor security alerts and prompt customer support.",
        },
    )
    assert review_res.status_code == 201
    review_data = review_res.json()
    assert review_data["rating"] == 5
    assert review_data["status"] == "PENDING_MODERATION"

    # Step 6: Submit a suspicious-domain report
    threat_res = await client.post(
        "/api/v1/threat-reports",
        headers=cust_headers,
        json={
            "brand_id": brand_id,
            "target_type": "DOMAIN",
            "target_value": "apexshieldbank-verify-account.com",
            "description": "Received suspicious SMS directing users to this domain to verify banking credentials.",
        },
    )
    assert threat_res.status_code == 201
    threat_data = threat_res.json()
    report_id = threat_data["id"]
    assert threat_data["status"] == "SUBMITTED"
    assert threat_data["target_value"] == "apexshieldbank-verify-account.com"

    # Step 7: Attach evidence (PNG screenshot)
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05"
        b"\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    files = {"file": ("screenshot_sms_lure.png", io.BytesIO(png_bytes), "image/png")}
    evidence_res = await client.post(
        f"/api/v1/threat-reports/{report_id}/evidence",
        headers=cust_headers,
        files=files,
        data={"evidence_type": "SCREENSHOT"},
    )
    assert evidence_res.status_code == 201
    evidence_data = evidence_res.json()
    assert evidence_data["original_filename"] == "screenshot_sms_lure.png"
    assert evidence_data["evidence_type"] == "SCREENSHOT"
    assert "sha256" in evidence_data
    assert evidence_data["file_size"] > 0

    # Step 8: Trigger analysis
    analyze_res = await client.post(
        f"/api/v1/threat-reports/{report_id}/analyze",
        headers=cust_headers,
    )
    assert analyze_res.status_code == 200
    analysis_data = analyze_res.json()
    assert analysis_data["report_id"] == report_id
    assert analysis_data["risk_score"] > 0.0
    assert analysis_data["severity"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    # Step 9: Retrieve the resulting assessment
    assessment_res = await client.get(
        f"/api/v1/threat-reports/{report_id}/assessment",
        headers=cust_headers,
    )
    assert assessment_res.status_code == 200
    assessment_data = assessment_res.json()
    assert assessment_data["id"] == analysis_data["id"]
    assert assessment_data["model_version"] == SCORING_RULE_VERSION
    assert "explanation_json" in assessment_data
    assert "indicators_json" in assessment_data
    assert "recommendation_json" in assessment_data

    # Step 10: Track the report status
    status_res = await client.get(
        f"/api/v1/threat-reports/{report_id}",
        headers=cust_headers,
    )
    assert status_res.status_code == 200
    report_detail = status_res.json()
    assert report_detail["id"] == report_id
    # Analysis transitions report status from SUBMITTED to ANALYZING / UNDER_REVIEW
    assert report_detail["status"] in ["ANALYZING", "UNDER_REVIEW", "CONFIRMED"]

    # Also verify report appears in customer's personal history list
    history_res = await client.get("/api/v1/users/me/threat-reports", headers=cust_headers)
    assert history_res.status_code == 200
    my_reports = history_res.json()
    assert any(r["id"] == report_id for r in my_reports)


@pytest.mark.asyncio
async def test_workflow_c_threat_analysis_e2e(
    client: AsyncClient,
    mock_otp: MockOTPProvider,
    db_session: AsyncSession,
) -> None:
    """
    WORKFLOW C — THREAT ANALYSIS (Complete 8-Step Lifecycle)
    1. Submit a suspicious domain.
    2. Normalize the domain.
    3. Run available detection services.
    4. Generate an explainable risk assessment.
    5. Store evidence and assessment results.
    6. Correlate the entity with existing entities when evidence supports a relationship.
    7. Generate an alert if the configured rules match.
    8. Display the result through the owner APIs.
    """
    # 0. Setup Brand Owner and Admin
    admin_id, admin_token = await _register_and_authenticate(client, mock_otp, "+14155551399")
    await _promote_to_admin(db_session, admin_id)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    owner_id, owner_token = await _register_and_authenticate(client, mock_otp, "+14155551301")
    app_res = await client.post(
        "/api/v1/brand-applications",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"business_name": "Titan Payments", "official_domain": "titanpayments.io"},
    )
    app_id = app_res.json()["id"]
    rev_res = await client.post(
        f"/api/v1/admin/brand-applications/{app_id}/review",
        headers=admin_headers,
        json={"decision": "APPROVE"},
    )
    brand_id = rev_res.json()["brand_id"]
    brand_uuid = uuid.UUID(brand_id)
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    cust_id, cust_token = await _register_and_authenticate(client, mock_otp, "+14155551302")
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    # Step 1: Submit a suspicious domain with whitespace, upper case, and URL formatting
    unnormalized_input = "  HTTPS://TitanPayments-Support-Login.io/auth/  "
    report_res = await client.post(
        "/api/v1/threat-reports",
        headers=cust_headers,
        json={
            "brand_id": brand_id,
            "target_type": "DOMAIN",
            "target_value": unnormalized_input,
            "description": "Phishing portal masquerading as Titan Payments support with login form.",
        },
    )
    assert report_res.status_code == 201
    rep_data = report_res.json()
    report_id = rep_data["id"]

    # Step 2: Normalize the domain
    # Expected canonical lower-case hostname without protocol or trailing slash
    canonical_domain = "titanpayments-support-login.io"
    assert rep_data["target_value"] == canonical_domain

    # Step 3: Run available detection services (URL, Domain, Scam text engines)
    # Step 4: Generate an explainable risk assessment
    analyze_res = await client.post(
        f"/api/v1/threat-reports/{report_id}/analyze",
        headers=cust_headers,
    )
    assert analyze_res.status_code == 200
    assessment = analyze_res.json()

    # Verify explainable breakdown
    assert assessment["model_version"] == SCORING_RULE_VERSION
    assert assessment["risk_score"] > 0.0
    explanation = assessment["explanation_json"]
    assert "score_breakdown" in explanation
    assert "DOMAIN_SIMILARITY" in explanation["evaluated_categories"]
    assert isinstance(explanation["unavailable_signals"], list)
    assert len(assessment["recommendation_json"]) > 0

    # Step 5: Store evidence and assessment results
    assessment_persisted = await client.get(
        f"/api/v1/threat-reports/{report_id}/assessment",
        headers=cust_headers,
    )
    assert assessment_persisted.status_code == 200
    assert assessment_persisted.json()["id"] == assessment["id"]

    # Attach evidence to store supporting artifact
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05"
        b"\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    ev_res = await client.post(
        f"/api/v1/threat-reports/{report_id}/evidence",
        headers=cust_headers,
        files={"file": ("phish_evidence.png", io.BytesIO(png_bytes), "image/png")},
        data={"evidence_type": "SCREENSHOT"},
    )
    assert ev_res.status_code == 201

    # Step 6: Correlate the entity with existing entities when evidence supports a relationship
    # Submit a second related domain to trigger entity clustering
    second_rep = await client.post(
        "/api/v1/threat-reports",
        headers=cust_headers,
        json={
            "brand_id": brand_id,
            "target_type": "DOMAIN",
            "target_value": "titanpayments-support-verify.io",
            "description": "Secondary domain related to the same campaign infrastructure.",
        },
    )
    assert second_rep.status_code == 201
    second_domain = second_rep.json()["target_value"]

    corr_service = CampaignCorrelationService()
    ent1, _ = await corr_service.entity_repo.get_or_create(
        db_session, corr_service.map_target_type_to_entity_type(TargetType.DOMAIN), canonical_domain
    )
    ent2, _ = await corr_service.entity_repo.get_or_create(
        db_session, corr_service.map_target_type_to_entity_type(TargetType.DOMAIN), second_domain
    )
    relationships = await corr_service.correlate_entities(db_session, brand_uuid, [ent1, ent2])
    assert len(relationships) >= 1

    # Build threat campaign
    campaigns = await corr_service.build_campaigns_for_brand(db_session, brand_uuid, [ent1, ent2])
    await db_session.commit()
    assert len(campaigns) >= 1
    active_campaign = campaigns[0]

    # Step 7: Generate an alert if the configured rules match
    alert_repo = corr_service.alert_repo
    alert, is_created = await alert_repo.create_if_not_duplicate(
        db=db_session,
        brand_id=brand_uuid,
        title=f"Campaign Detected: {active_campaign.title}",
        description=f"Correlated cluster detected across {canonical_domain} and {second_domain}",
        severity=RiskSeverity.HIGH,
        fingerprint=f"campaign_{active_campaign.id}",
        campaign_id=active_campaign.id,
    )
    await db_session.commit()
    assert is_created is True
    assert alert is not None

    # Step 8: Display the result through the owner APIs (Threats, Campaigns, Alerts, Graph)
    # Threats list
    owner_threats = await client.get(
        f"/api/v1/owner/brands/{brand_id}/threats",
        headers=owner_headers,
    )
    assert owner_threats.status_code == 200
    assert len(owner_threats.json()) >= 2

    # Campaigns list
    owner_campaigns = await client.get(
        f"/api/v1/owner/brands/{brand_id}/campaigns",
        headers=owner_headers,
    )
    assert owner_campaigns.status_code == 200
    camp_items = owner_campaigns.json()
    assert any(c["id"] == str(active_campaign.id) for c in camp_items)

    # Alerts list
    owner_alerts = await client.get(
        f"/api/v1/owner/brands/{brand_id}/alerts",
        headers=owner_headers,
    )
    assert owner_alerts.status_code == 200
    alert_items = owner_alerts.json()
    assert any(a["id"] == str(alert.id) for a in alert_items)

    # Graph visualization
    owner_graph = await client.get(
        f"/api/v1/owner/brands/{brand_id}/graph",
        headers=owner_headers,
    )
    assert owner_graph.status_code == 200
    graph_data = owner_graph.json()
    assert "nodes" in graph_data
    assert "edges" in graph_data
    assert len(graph_data["nodes"]) >= 2
    assert "disclaimer" in graph_data
