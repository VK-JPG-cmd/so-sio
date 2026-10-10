"""
Phase 5 Integration Tests: Threat Correlation Engine

Validates the complete end-to-end correlation pipeline:
1. Auto-entity ingestion when threat reports are submitted.
2. POST /owner/brands/{brand_id}/correlate triggers full correlation pipeline.
3. GET /owner/brands/{brand_id}/campaigns/{campaign_id} returns campaign detail.
4. Duplicate alert suppression across two correlation runs.
5. Cross-brand isolation: owner cannot trigger correlation for foreign brand.
6. CorrelationRunResponse is schema-valid and has expected counts.
"""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

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


async def _setup_verified_brand(
    client: AsyncClient,
    mock_otp: MockOTPProvider,
    admin_token: str,
    phone: str,
    business_name: str,
    domain: str,
) -> tuple[str, str]:
    """Register and approve a brand, returning (brand_id, owner_token)."""
    _, owner_token = await _create_user(client, mock_otp, phone)
    app_res = await client.post(
        "/api/v1/brand-applications",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"business_name": business_name, "official_domain": domain},
    )
    assert app_res.status_code == 201, app_res.text
    app_id = app_res.json()["id"]

    review_res = await client.post(
        f"/api/v1/admin/brand-applications/{app_id}/review",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"decision": "APPROVE", "notes": "Test approval"},
    )
    assert review_res.status_code == 200, review_res.text
    return str(review_res.json()["brand_id"]), owner_token


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

async def test_entity_auto_ingested_on_report_submission(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """
    Verify that submitting a threat report automatically indexes the entity
    so the correlation engine can see it without a manual ingestion call.
    """
    _, admin_token = await _create_admin(client, mock_otp, "+15550001001", db_session)
    brand_id, owner_token = await _setup_verified_brand(
        client, mock_otp, admin_token, "+15550001002", "AutoIngest Corp", "autoingest-corp.com"
    )
    _, cust_token = await _create_user(client, mock_otp, "+15550001003")

    # Submit a single domain report
    rep = await client.post(
        "/api/v1/threat-reports",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={
            "brand_id": brand_id,
            "target_type": "DOMAIN",
            "target_value": "autoingest-phish.com",
            "description": "Phishing domain imitating AutoIngest Corp.",
        },
    )
    assert rep.status_code == 201, rep.text

    # With only 1 entity the correlate endpoint should acknowledge it but form no campaigns.
    corr_res = await client.post(
        f"/api/v1/owner/brands/{brand_id}/correlate",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert corr_res.status_code == 200, corr_res.text
    body = corr_res.json()
    assert body["entities_ingested"] == 1
    assert body["relationships_created"] == 0
    assert body["campaigns_created"] == 0
    assert "Insufficient" in body["message"]


async def test_correlate_endpoint_builds_campaigns_and_alerts(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """
    Full correlation pipeline via the API:
    1. Submit two lexically-similar domain reports (will form a SIMILAR_DOMAIN relationship).
    2. POST /correlate -> campaigns_created >= 1, alerts_created >= 1.
    3. GET /campaigns lists the campaign.
    4. GET /campaigns/{id} returns full campaign detail with >= 2 member entities.
    5. GET /alerts has at least one alert linked to the campaign.
    """
    _, admin_token = await _create_admin(client, mock_otp, "+15550002001", db_session)
    brand_id, owner_token = await _setup_verified_brand(
        client, mock_otp, admin_token, "+15550002002", "ThreatCorp Alpha", "threatcorpalpha.com"
    )
    _, cust_token = await _create_user(client, mock_otp, "+15550002003")

    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    # Submit two reports with lexically similar domains (>= 75% ratio expected)
    for domain in ("threatcorpalpha-login.com", "threatcorpalpha-portal.com"):
        r = await client.post(
            "/api/v1/threat-reports",
            headers=cust_headers,
            json={
                "brand_id": brand_id,
                "target_type": "DOMAIN",
                "target_value": domain,
                "description": f"Lookalike domain: {domain}",
            },
        )
        assert r.status_code == 201, r.text

    # Trigger correlation
    corr_res = await client.post(
        f"/api/v1/owner/brands/{brand_id}/correlate", headers=owner_headers
    )
    assert corr_res.status_code == 200, corr_res.text
    body = corr_res.json()
    assert body["entities_ingested"] == 2
    assert body["relationships_created"] >= 1
    assert body["campaigns_created"] >= 1
    assert body["alerts_created"] >= 1

    # GET /campaigns
    camps_res = await client.get(
        f"/api/v1/owner/brands/{brand_id}/campaigns", headers=owner_headers
    )
    assert camps_res.status_code == 200, camps_res.text
    camps = camps_res.json()
    assert len(camps) >= 1

    campaign_id = camps[0]["id"]

    # GET /campaigns/{campaign_id} — detail with member entities
    detail_res = await client.get(
        f"/api/v1/owner/brands/{brand_id}/campaigns/{campaign_id}", headers=owner_headers
    )
    assert detail_res.status_code == 200, detail_res.text
    detail = detail_res.json()
    assert detail["id"] == campaign_id
    assert len(detail["memberships"]) >= 2

    # GET /alerts — must show alert linked to the campaign
    alerts_res = await client.get(
        f"/api/v1/owner/brands/{brand_id}/alerts", headers=owner_headers
    )
    assert alerts_res.status_code == 200, alerts_res.text
    alerts = alerts_res.json()
    assert len(alerts) >= 1
    assert any(a["campaign_id"] == campaign_id for a in alerts)


async def test_duplicate_correlation_run_suppresses_alerts(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """
    Running /correlate twice must NOT create duplicate alerts for the same
    unresolved campaign (deduplication fingerprint enforcement).
    """
    _, admin_token = await _create_admin(client, mock_otp, "+15550003001", db_session)
    brand_id, owner_token = await _setup_verified_brand(
        client, mock_otp, admin_token, "+15550003002", "DedupBrandCo", "dedup-brand-co.com"
    )
    _, cust_token = await _create_user(client, mock_otp, "+15550003003")

    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    for domain in ("dedup-brand-co-login.com", "dedup-brand-co-portal.com"):
        r = await client.post(
            "/api/v1/threat-reports",
            headers=cust_headers,
            json={
                "brand_id": brand_id,
                "target_type": "DOMAIN",
                "target_value": domain,
                "description": f"Lookalike: {domain}",
            },
        )
        assert r.status_code == 201

    # First correlation run
    await client.post(f"/api/v1/owner/brands/{brand_id}/correlate", headers=owner_headers)
    alerts_after_first = (
        await client.get(f"/api/v1/owner/brands/{brand_id}/alerts", headers=owner_headers)
    ).json()
    count_first = len(alerts_after_first)
    assert count_first >= 1

    # Second correlation run
    await client.post(f"/api/v1/owner/brands/{brand_id}/correlate", headers=owner_headers)
    alerts_after_second = (
        await client.get(f"/api/v1/owner/brands/{brand_id}/alerts", headers=owner_headers)
    ).json()
    # Alert count must be identical — no duplicates
    assert len(alerts_after_second) == count_first


async def test_correlate_requires_brand_ownership(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """
    Owner B and a regular customer must receive 403 when trying to trigger
    correlation for Brand A. Admin must receive 200.
    """
    _, admin_token = await _create_admin(client, mock_otp, "+15550004001", db_session)
    brand_a_id, _ = await _setup_verified_brand(
        client, mock_otp, admin_token, "+15550004002", "Brand Isolation A", "brand-iso-a.com"
    )
    _, owner_b_token = await _setup_verified_brand(
        client, mock_otp, admin_token, "+15550004003", "Brand Isolation B", "brand-iso-b.com"
    )
    _, cust_token = await _create_user(client, mock_otp, "+15550004004")

    # Owner B -> 403
    res_b = await client.post(
        f"/api/v1/owner/brands/{brand_a_id}/correlate",
        headers={"Authorization": f"Bearer {owner_b_token}"},
    )
    assert res_b.status_code == 403, res_b.text

    # Customer -> 403
    res_cust = await client.post(
        f"/api/v1/owner/brands/{brand_a_id}/correlate",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert res_cust.status_code == 403, res_cust.text

    # Admin -> 200 (no entities yet, but request is authorized)
    res_admin = await client.post(
        f"/api/v1/owner/brands/{brand_a_id}/correlate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin.status_code == 200, res_admin.text


async def test_campaign_detail_404_for_nonexistent_campaign(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """
    Requesting a campaign that does not belong to the brand must return 404.
    """
    _, admin_token = await _create_admin(client, mock_otp, "+15550005001", db_session)
    brand_id, owner_token = await _setup_verified_brand(
        client, mock_otp, admin_token, "+15550005002", "CampaignBrand", "campaign-brand.com"
    )

    fake_campaign_id = str(uuid.uuid4())
    res = await client.get(
        f"/api/v1/owner/brands/{brand_id}/campaigns/{fake_campaign_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res.status_code == 404, res.text
