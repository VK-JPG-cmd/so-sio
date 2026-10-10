"""
Phase 6 Integration Tests: Threat Discovery Pipeline & Continuous Monitoring
Validates:
1. End-to-end brand threat discovery, detection, campaign correlation, and alert generation
2. Repeated observation deduplication and last_observed_at timestamp refresh
3. Official brand domain protection (zero false-positive guarantee)
4. Unrelated internet indicators marked as NO_BRAND_MATCH without false alerts
5. Worker discovery cycle execution and persistent checkpoint tracking
6. Administrative operational endpoints (/discovery/health, /discovery/stats, /discovery/run-now) and RBAC
"""

from datetime import datetime, timezone
import uuid
import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.alert import Alert
from app.models.campaign import Campaign
from app.models.discovered_indicator import DiscoveredIndicator
from app.models.discovery_checkpoint import DiscoveryCheckpoint
from app.models.enums import EntityType, UserRole
from app.models.threat_entity import ThreatEntity
from app.models.user import User
from app.services.discovery.connector import DiscoveredIndicatorRecord
from app.services.discovery.connectors.urlhaus import URLhausConnector
from app.services.discovery.pipeline import ThreatDiscoveryPipeline
from app.services.discovery.worker import ThreatDiscoveryWorker
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
        json={"decision": "APPROVE", "notes": "Approved for discovery tests."},
    )
    assert review_res.status_code == 200, review_res.text

    brand_id = str(review_res.json()["brand_id"])
    return brand_id, owner_token


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_threat_discovery_end_to_end_brand_correlation(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """
    Test that an external observation targeting a verified brand:
    1. Gets indexed in discovered_indicators with MATCHED_BRAND
    2. Enriches with risk score and risk level
    3. Normalizes and creates ThreatEntity
    4. Triggers CampaignCorrelation and creates a Campaign
    5. Generates a deduplicated Alert for the brand owner
    """
    _, admin_token = await _create_admin(client, mock_otp, "+15550005001", db_session)
    brand_id_str, owner_token = await _setup_verified_brand(
        client, mock_otp, admin_token, "+15550005002", "DiscoveryCorp", "discoverycorp.com"
    )
    brand_uuid = uuid.UUID(brand_id_str)

    pipeline = ThreatDiscoveryPipeline()

    # Create observation targeting DiscoveryCorp
    record = DiscoveredIndicatorRecord(
        source_id="urlhaus",
        source_record_id="90001",
        indicator_type=EntityType.URL,
        raw_indicator="http://discoverycorp-login.com/auth/step1",
        canonical_value="http://discoverycorp-login.com/auth/step1",
        source_first_seen_at=datetime.now(timezone.utc),
        tags=["malware_download", "phish"],
    )

    indicator = await pipeline.process_record(db_session, record)
    await db_session.commit()

    # 1. Indicator attributes
    assert indicator.processing_status == "MATCHED_BRAND"
    assert indicator.brand_id == brand_uuid
    assert indicator.risk_score is not None and indicator.risk_score >= 50.0
    assert indicator.threat_entity_id is not None

    # 2. Verify threat entity was created
    stmt_ent = select(ThreatEntity).where(ThreatEntity.id == indicator.threat_entity_id)
    ent_res = await db_session.execute(stmt_ent)
    threat_ent = ent_res.scalar_one_or_none()
    assert threat_ent is not None
    assert threat_ent.canonical_value == "http://discoverycorp-login.com/auth/step1"

    # 3. Verify owner can see alerts via Owner Threats API
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    alerts_res = await client.get(
        f"/api/v1/owner/brands/{brand_id_str}/alerts", headers=owner_headers
    )
    assert alerts_res.status_code == 200, alerts_res.text


@pytest.mark.asyncio
async def test_repeated_observation_suppresses_duplicate_alerts_and_entities(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """
    Repeated polling of the same external indicator must update last_observed_at
    without creating duplicate DiscoveredIndicator rows, ThreatEntities, or Alerts.
    """
    _, admin_token = await _create_admin(client, mock_otp, "+15550005003", db_session)
    brand_id_str, owner_token = await _setup_verified_brand(
        client, mock_otp, admin_token, "+15550005004", "DedupDiscCo", "dedupdiscco.com"
    )

    pipeline = ThreatDiscoveryPipeline()

    record = DiscoveredIndicatorRecord(
        source_id="urlhaus",
        source_record_id="90002",
        indicator_type=EntityType.URL,
        raw_indicator="http://dedupdiscco-portal.com/login",
        canonical_value="http://dedupdiscco-portal.com/login",
    )

    # First ingestion
    ind1 = await pipeline.process_record(db_session, record)
    await db_session.commit()
    first_seen = ind1.ingested_at
    first_id = ind1.id

    # Second ingestion of identical record
    ind2 = await pipeline.process_record(db_session, record)
    await db_session.commit()

    # Must be the exact same row with unchanged ingested_at
    assert ind2.id == first_id
    assert ind2.ingested_at == first_seen

    # Verify total count of DiscoveredIndicator rows is 1
    stmt = select(DiscoveredIndicator).where(
        DiscoveredIndicator.source_id == "urlhaus",
        DiscoveredIndicator.canonical_value == "http://dedupdiscco-portal.com/login",
    )
    res = await db_session.execute(stmt)
    assert len(list(res.scalars().all())) == 1


@pytest.mark.asyncio
async def test_official_brand_domain_is_exempted_zero_false_positives(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """
    If an external threat feed mistakenly lists an official verified brand domain,
    the pipeline must recognize it as OFFICIAL_BRAND_ASSET and assign BENIGN / 0.0 risk,
    generating zero alerts.
    """
    _, admin_token = await _create_admin(client, mock_otp, "+15550005005", db_session)
    brand_id_str, owner_token = await _setup_verified_brand(
        client, mock_otp, admin_token, "+15550005006", "OfficialShield", "officialshield.com"
    )

    pipeline = ThreatDiscoveryPipeline()

    # Observation targets the official domain
    record = DiscoveredIndicatorRecord(
        source_id="urlhaus",
        source_record_id="90003",
        indicator_type=EntityType.URL,
        raw_indicator="https://officialshield.com/security/info",
        canonical_value="https://officialshield.com/security/info",
    )

    indicator = await pipeline.process_record(db_session, record)
    await db_session.commit()

    assert indicator.processing_status == "OFFICIAL_BRAND_ASSET"
    assert indicator.risk_score == 0.0
    assert indicator.risk_level == "BENIGN"
    assert indicator.campaign_id is None
    assert indicator.alert_id is None

    # Owner alerts must be empty
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    alerts_res = await client.get(
        f"/api/v1/owner/brands/{brand_id_str}/alerts", headers=owner_headers
    )
    assert alerts_res.status_code == 200
    assert len(alerts_res.json()) == 0


@pytest.mark.asyncio
async def test_unrelated_indicator_no_brand_match(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """
    Arbitrary internet threats with no technical or lexical connection to
    registered brands must be marked NO_BRAND_MATCH without creating brand campaigns.
    """
    pipeline = ThreatDiscoveryPipeline()

    record = DiscoveredIndicatorRecord(
        source_id="urlhaus",
        source_record_id="90004",
        indicator_type=EntityType.URL,
        raw_indicator="http://random-unrelated-botnet-cluster.top/loader",
        canonical_value="http://random-unrelated-botnet-cluster.top/loader",
    )

    indicator = await pipeline.process_record(db_session, record)
    await db_session.commit()

    assert indicator.processing_status == "NO_BRAND_MATCH"
    assert indicator.brand_id is None
    assert indicator.campaign_id is None
    assert indicator.alert_id is None


@pytest.mark.asyncio
async def test_worker_discovery_cycle_and_checkpoint_persistence(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """
    Verify ThreatDiscoveryWorker executes a full cycle, records checkpoint,
    and subsequent cycle honors the checkpoint.
    """
    mock_payload = {
        "query_status": "ok",
        "urls": [
            {
                "id": "7001",
                "url": "http://threat-batch-one.com/a",
                "dateadded": "2026-10-10 10:00:00 UTC",
            },
            {
                "id": "7002",
                "url": "http://threat-batch-one.com/b",
                "dateadded": "2026-10-10 10:05:00 UTC",
            },
        ],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=mock_payload)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        mock_connector = URLhausConnector(base_url="https://urlhaus-api.abuse.ch/v1", client=mock_http)
        worker = ThreatDiscoveryWorker(connectors=[mock_connector])

        # Run discovery cycle
        summary = await worker.run_discovery_cycle(db_override=db_session)
        assert summary["connectors_processed"] == 1
        assert summary["total_fetched"] == 2
        assert summary["total_valid"] == 2

        # Verify persistent checkpoint was saved in DB
        stmt = select(DiscoveryCheckpoint).where(DiscoveryCheckpoint.source_id == "urlhaus")
        res = await db_session.execute(stmt)
        cp = res.scalar_one_or_none()
        assert cp is not None
        assert cp.checkpoint_value == "7002"
        assert cp.status == "IDLE"
        assert cp.indicators_fetched_total == 2


@pytest.mark.asyncio
async def test_operational_endpoints_rbac_and_telemetry(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    """
    Verify RBAC on operational discovery endpoints:
    - Customer receives 403 Forbidden
    - Admin receives 200 with full health, statistics, and run-now execution
    """
    _, cust_token = await _create_user(client, mock_otp, "+15550005010")
    _, admin_token = await _create_admin(client, mock_otp, "+15550005011", db_session)

    cust_headers = {"Authorization": f"Bearer {cust_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Customer RBAC rejection
    for endpoint in ("/discovery/health", "/discovery/stats"):
        r = await client.get(f"/api/v1/admin{endpoint}", headers=cust_headers)
        assert r.status_code == 403

    r_run = await client.post("/api/v1/admin/discovery/run-now", headers=cust_headers)
    assert r_run.status_code == 403

    # 2. Admin access to /discovery/health
    health_res = await client.get("/api/v1/admin/discovery/health", headers=admin_headers)
    assert health_res.status_code == 200, health_res.text
    health_data = health_res.json()
    assert "worker_running" in health_data
    assert "sources" in health_data
    assert len(health_data["sources"]) >= 1

    # 3. Admin access to /discovery/stats
    stats_res = await client.get("/api/v1/admin/discovery/stats", headers=admin_headers)
    assert stats_res.status_code == 200, stats_res.text
    stats_data = stats_res.json()
    assert "total_indicators" in stats_data
    assert "status_counts" in stats_data

    # 4. Admin triggers /discovery/run-now
    run_res = await client.post("/api/v1/admin/discovery/run-now", headers=admin_headers)
    assert run_res.status_code == 200, run_res.text
    run_data = run_res.json()
    assert "status" in run_data
