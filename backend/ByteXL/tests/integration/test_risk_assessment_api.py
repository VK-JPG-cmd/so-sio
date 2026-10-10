"""
Integration tests for Phase 6: Unified Risk Assessment and Explainability API
Endpoints tested:
- POST /api/v1/threat-reports/{report_id}/analyze
- GET /api/v1/threat-reports/{report_id}/assessment

Validates:
- End-to-end integration with Phase 5 detection services
- Ownership and authorization enforcement
- Explainability breakdown and unavailable signals
- Actionable recommendations
- Report investigation lifecycle transition
"""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.enums import ThreatReportStatus, UserRole
from app.models.user import User
from app.services.otp_provider import MockOTPProvider
from app.services.scoring.config import SCORING_RULE_VERSION


async def _create_user(client: AsyncClient, mock_otp: MockOTPProvider, phone: str) -> tuple[str, str]:
    """Helper to authenticate a customer user."""
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
    domain: str = "acmefinance.com",
) -> str:
    """Helper to register and administratively approve a brand."""
    _, owner_token = await _create_user(client, mock_otp, phone)
    app_res = await client.post(
        "/api/v1/brand-applications",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"business_name": "Acme Finance Corp", "official_domain": domain},
    )
    app_id = app_res.json()["id"]

    review_res = await client.post(
        f"/api/v1/admin/brand-applications/{app_id}/review",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"decision": "APPROVE", "notes": "Verified business entity"},
    )
    return str(review_res.json()["brand_id"])


async def test_analyze_domain_threat_report_flow(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """Verify end-to-end domain threat report analysis with explainability and status update."""
    _, admin_token = await _create_admin(client, mock_otp, "+14155559001", db_session)
    brand_id = await _setup_verified_brand(client, mock_otp, admin_token, "+14155559002", "acmefinance.com")
    _, cust_token = await _create_user(client, mock_otp, "+14155559003")

    # 1. Submit a DOMAIN threat report with visual lookalike/typosquat
    report_res = await client.post(
        "/api/v1/threat-reports",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={
            "brand_id": brand_id,
            "target_type": "DOMAIN",
            "target_value": "acmefinance-login.com",  # High similarity + suspicious keyword
            "description": "Suspected lookalike credential harvesting domain targeting Acme Finance.",
        },
    )
    assert report_res.status_code == 201
    report_id = report_res.json()["id"]

    # 2. Before analysis, GET /assessment returns 404
    get_early = await client.get(
        f"/api/v1/threat-reports/{report_id}/assessment",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert get_early.status_code == 404

    # 3. Customer triggers analysis: POST /threat-reports/{id}/analyze
    analyze_res = await client.post(
        f"/api/v1/threat-reports/{report_id}/analyze",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert analyze_res.status_code == 200
    data = analyze_res.json()

    assert data["report_id"] == report_id
    assert data["model_version"] == SCORING_RULE_VERSION
    assert 0.0 <= data["risk_score"] <= 100.0
    assert data["risk_score"] > 0.0  # Indicators detected
    assert data["severity"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    # Explainability breakdown checks
    explanation = data["explanation_json"]
    assert explanation["scoring_rule_version"] == SCORING_RULE_VERSION
    assert "score_breakdown" in explanation
    assert "DOMAIN_SIMILARITY" in explanation["evaluated_categories"]
    assert len(explanation["unavailable_signals"]) > 0

    # Indicators list check
    indicators = data["indicators_json"]
    assert any(i["category"] == "DOMAIN_SIMILARITY" for i in indicators)

    # Recommendations check
    recs = data["recommendation_json"]
    assert any(r["action"] == "VERIFY_DOMAIN_OWNERSHIP" for r in recs)

    # 4. Verify GET /assessment returns identical persisted record
    get_res = await client.get(
        f"/api/v1/threat-reports/{report_id}/assessment",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert get_res.status_code == 200
    assert get_res.json()["id"] == data["id"]
    assert get_res.json()["risk_score"] == data["risk_score"]

    # 5. Verify ThreatReport status transitioned to UNDER_REVIEW
    detail_res = await client.get(
        f"/api/v1/threat-reports/{report_id}",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert detail_res.status_code == 200
    assert detail_res.json()["status"] == ThreatReportStatus.UNDER_REVIEW.value


async def test_analyze_scam_text_threat_report(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """Verify scam text risk assessment evaluates ML model and urgency/credential indicators."""
    _, cust_token = await _create_user(client, mock_otp, "+14155559004")

    report_res = await client.post(
        "/api/v1/threat-reports",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={
            "target_type": "SCAM_TEXT",
            "target_value": "URGENT: Your bank account is suspended immediately. Confirm your password and send OTP.",
            "description": "Phishing SMS received claiming account lockout.",
        },
    )
    assert report_res.status_code == 201
    report_id = report_res.json()["id"]

    analyze_res = await client.post(
        f"/api/v1/threat-reports/{report_id}/analyze",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert analyze_res.status_code == 200
    data = analyze_res.json()

    assert data["risk_score"] > 0.0
    indicators = data["indicators_json"]
    assert any(i["category"] == "SCAM_AND_CREDENTIAL_HARVESTING" for i in indicators)


async def test_analyze_and_assessment_authorization_enforced(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """Verify cross-customer isolation on POST /analyze and GET /assessment (403 Forbidden)."""
    _, owner_token = await _create_user(client, mock_otp, "+14155559005")
    _, attacker_token = await _create_user(client, mock_otp, "+14155559006")
    _, admin_token = await _create_admin(client, mock_otp, "+14155559007", db_session)

    # 1. Owner creates report
    report_res = await client.post(
        "/api/v1/threat-reports",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "target_type": "DOMAIN",
            "target_value": "test-phish-domain.com",
            "description": "Private customer threat report",
        },
    )
    report_id = report_res.json()["id"]

    # 2. Attacker attempts to analyze owner's report -> 403 Forbidden
    res_analyze_blocked = await client.post(
        f"/api/v1/threat-reports/{report_id}/analyze",
        headers={"Authorization": f"Bearer {attacker_token}"},
    )
    assert res_analyze_blocked.status_code == 403

    # 3. Owner analyzes report -> 200 OK
    res_owner_analyze = await client.post(
        f"/api/v1/threat-reports/{report_id}/analyze",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res_owner_analyze.status_code == 200

    # 4. Attacker attempts to retrieve owner's assessment -> 403 Forbidden
    res_get_blocked = await client.get(
        f"/api/v1/threat-reports/{report_id}/assessment",
        headers={"Authorization": f"Bearer {attacker_token}"},
    )
    assert res_get_blocked.status_code == 403

    # 5. Administrator can view owner's assessment -> 200 OK
    res_admin_get = await client.get(
        f"/api/v1/threat-reports/{report_id}/assessment",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin_get.status_code == 200
    assert res_admin_get.json()["report_id"] == report_id


async def test_analyze_social_profile_threat_report_flow(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """Verify end-to-end SOCIAL_PROFILE threat report analysis without AttributeError."""
    _, admin_token = await _create_admin(client, mock_otp, "+14155559010", db_session)
    brand_id = await _setup_verified_brand(client, mock_otp, admin_token, "+14155559011", "acmepayments.com")
    _, cust_token = await _create_user(client, mock_otp, "+14155559012")

    # 1. Submit a SOCIAL_PROFILE threat report with bio claims
    report_res = await client.post(
        "/api/v1/threat-reports",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={
            "brand_id": brand_id,
            "target_type": "SOCIAL_PROFILE",
            "target_value": "@acmefinance_support",
            "description": "Official support team for Acme Finance. DM us immediately.",
        },
    )
    assert report_res.status_code == 201
    report_id = report_res.json()["id"]

    # 2. Analyze the report -> must return 200 OK without AttributeError
    analyze_res = await client.post(
        f"/api/v1/threat-reports/{report_id}/analyze",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert analyze_res.status_code == 200
    data = analyze_res.json()
    assert data["report_id"] == report_id
    assert data["risk_score"] > 0.0
    assert data["severity"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert any(ind["signal_type"] == "PROFILE_HANDLE_IMPERSONATION" for ind in data["indicators_json"])

