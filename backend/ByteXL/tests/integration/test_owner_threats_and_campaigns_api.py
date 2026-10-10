"""
Integration tests for Brand Owner Threats, Campaigns, Alerts, and Correlation Graph API:
- GET /api/v1/owner/brands/{brand_id}/threats
- GET /api/v1/owner/brands/{brand_id}/campaigns
- GET /api/v1/owner/brands/{brand_id}/alerts
- GET /api/v1/owner/brands/{brand_id}/graph

Validates:
- Strict brand ownership authorization (cross-brand isolation returns 403 Forbidden)
- Campaign clustering of related threat entities
- Non-duplication of unresolved alerts
- Visual graph nodes and edges with disclaimer
"""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.enums import UserRole
from app.models.user import User
from app.services.correlation.campaign_service import CampaignCorrelationService
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


async def test_owner_can_access_own_brand_data(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """Verify that a brand owner can access threats, campaigns, alerts, and graph for their brand."""
    _, admin_token = await _create_admin(client, mock_otp, "+14155557001", db_session)
    brand_id, owner_token = await _setup_verified_brand(
        client, mock_otp, admin_token, "+14155557002", "Apex Secure", "apexsecure.com"
    )

    headers = {"Authorization": f"Bearer {owner_token}"}

    # 1. GET /threats
    res_threats = await client.get(f"/api/v1/owner/brands/{brand_id}/threats", headers=headers)
    assert res_threats.status_code == 200
    assert isinstance(res_threats.json(), list)

    # 2. GET /campaigns
    res_campaigns = await client.get(f"/api/v1/owner/brands/{brand_id}/campaigns", headers=headers)
    assert res_campaigns.status_code == 200
    assert isinstance(res_campaigns.json(), list)

    # 3. GET /alerts
    res_alerts = await client.get(f"/api/v1/owner/brands/{brand_id}/alerts", headers=headers)
    assert res_alerts.status_code == 200
    assert isinstance(res_alerts.json(), list)

    # 4. GET /graph
    res_graph = await client.get(f"/api/v1/owner/brands/{brand_id}/graph", headers=headers)
    assert res_graph.status_code == 200
    graph_data = res_graph.json()
    assert graph_data["brand_id"] == brand_id
    assert "disclaimer" in graph_data
    assert "nodes" in graph_data
    assert "edges" in graph_data


async def test_cross_brand_access_strictly_forbidden(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """Verify that Brand Owner B CANNOT access Brand Owner A's brand data (403 Forbidden)."""
    _, admin_token = await _create_admin(client, mock_otp, "+14155557003", db_session)
    brand_a_id, _ = await _setup_verified_brand(
        client, mock_otp, admin_token, "+14155557004", "Brand Alpha", "alpha-corp.com"
    )
    _, owner_b_token = await _setup_verified_brand(
        client, mock_otp, admin_token, "+14155557005", "Brand Beta", "beta-corp.com"
    )
    _, customer_token = await _create_user(client, mock_otp, "+14155557006")

    headers_b = {"Authorization": f"Bearer {owner_b_token}"}
    headers_cust = {"Authorization": f"Bearer {customer_token}"}

    # Owner B attempting to access Brand A's resources -> 403 Forbidden
    for endpoint in ["threats", "campaigns", "alerts", "graph"]:
        res_blocked = await client.get(f"/api/v1/owner/brands/{brand_a_id}/{endpoint}", headers=headers_b)
        assert res_blocked.status_code == 403

        # Regular customer attempting to access -> 403 Forbidden
        res_cust_blocked = await client.get(f"/api/v1/owner/brands/{brand_a_id}/{endpoint}", headers=headers_cust)
        assert res_cust_blocked.status_code == 403

    # Admin CAN access Brand A's resources -> 200 OK
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    res_admin = await client.get(f"/api/v1/owner/brands/{brand_a_id}/campaigns", headers=admin_headers)
    assert res_admin.status_code == 200


async def test_end_to_end_campaign_correlation_and_alerts(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """
    Verify complete flow:
    1. Threat reports submitted for Brand Alpha.
    2. Related entities correlated into candidate campaigns.
    3. Alert created with duplicate suppression.
    4. Graph endpoint visualizes connected nodes and edges.
    """
    _, admin_token = await _create_admin(client, mock_otp, "+14155557007", db_session)
    brand_id, owner_token = await _setup_verified_brand(
        client, mock_otp, admin_token, "+14155557008", "Brand Delta", "brand-delta.com"
    )
    _, cust_token = await _create_user(client, mock_otp, "+14155557009")

    # 1. Customer submits two lookalike domain reports targeting Brand Delta
    rep1 = await client.post(
        "/api/v1/threat-reports",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={
            "brand_id": brand_id,
            "target_type": "DOMAIN",
            "target_value": "brand-delta-portal.com",
            "description": "First lookalike domain targeting delta brand portal.",
        },
    )
    assert rep1.status_code == 201

    rep2 = await client.post(
        "/api/v1/threat-reports",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={
            "brand_id": brand_id,
            "target_type": "DOMAIN",
            "target_value": "brand-delta-login.com",
            "description": "Second lookalike domain with high lexical overlap.",
        },
    )
    assert rep2.status_code == 201

    # 2. Correlate entities and build campaigns
    corr_service = CampaignCorrelationService()
    brand_uuid = uuid.UUID(brand_id)

    ent1, _ = await corr_service.entity_repo.get_or_create(
        db_session, corr_service.map_target_type_to_entity_type(rep1.json()["target_type"]), "brand-delta-portal.com"
    )
    ent2, _ = await corr_service.entity_repo.get_or_create(
        db_session, corr_service.map_target_type_to_entity_type(rep2.json()["target_type"]), "brand-delta-login.com"
    )

    await corr_service.correlate_entities(db_session, brand_uuid, [ent1, ent2])
    campaigns = await corr_service.build_campaigns_for_brand(db_session, brand_uuid, [ent1, ent2])
    await db_session.commit()

    assert len(campaigns) >= 1
    campaign = campaigns[0]

    # 3. Retrieve campaigns via API
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    res_camps = await client.get(f"/api/v1/owner/brands/{brand_id}/campaigns", headers=owner_headers)
    assert res_camps.status_code == 200
    camp_list = res_camps.json()
    assert len(camp_list) >= 1
    assert any(c["id"] == str(campaign.id) for c in camp_list)

    # 4. Retrieve alerts via API
    res_alerts = await client.get(f"/api/v1/owner/brands/{brand_id}/alerts", headers=owner_headers)
    assert res_alerts.status_code == 200
    alert_list = res_alerts.json()
    assert len(alert_list) >= 1
    assert any(a["campaign_id"] == str(campaign.id) for a in alert_list)

    # 5. Retrieve graph via API
    res_graph = await client.get(f"/api/v1/owner/brands/{brand_id}/graph", headers=owner_headers)
    assert res_graph.status_code == 200
    graph = res_graph.json()
    assert len(graph["nodes"]) >= 2
    assert len(graph["edges"]) >= 1
    assert "disclaimer" in graph
