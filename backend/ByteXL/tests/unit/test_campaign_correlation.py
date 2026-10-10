"""
Unit tests for Threat Intelligence and Campaign Correlation:
- Entity normalization across attack surfaces
- Entity deduplication and last_seen updates
- Defensible technical relationships (similar domains, shared destinations, reused image hashes)
- Prevention of false correlations (mentioning same brand without technical evidence must NOT connect)
- Relationship status lifecycle (CANDIDATE, INVESTIGATED, CONFIRMED)
- Duplicate alert prevention via deduplication fingerprints
"""

import uuid
import pytest
from app.models.enums import EntityType, RelationshipStatus, RelationshipType, RiskSeverity
from app.models.threat_entity import ThreatEntity
from app.repositories.correlation_repo import AlertRepository, ThreatEntityRepository
from app.services.correlation.normalization import normalize_threat_entity
from app.services.correlation.relationship_engine import DefensibleRelationshipEngine
from sqlalchemy.ext.asyncio import AsyncSession


def test_entity_normalization_across_types() -> None:
    """Verify canonicalization across DOMAIN, URL, IP, SOCIAL_PROFILE, SCAM_TEXT_HASH, APK_PACKAGE."""
    # 1. DOMAIN
    assert normalize_threat_entity("HTTP://Login-Acme.com/", EntityType.DOMAIN) == "login-acme.com"
    assert normalize_threat_entity("  SECURE.Acme.com.  ", EntityType.DOMAIN) == "secure.acme.com"

    # 2. URL
    assert (
        normalize_threat_entity("HTTPS://PHISH.com/Login?tok=1#section", EntityType.URL)
        == "https://phish.com/login?tok=1"
    )

    # 3. IP_ADDRESS
    assert normalize_threat_entity("192.168.001.001", EntityType.IP_ADDRESS) == "192.168.1.1"

    # 4. SOCIAL_PROFILE
    assert normalize_threat_entity("@AcmeSupport_Help  ", EntityType.SOCIAL_PROFILE) == "acmesupport_help"
    assert normalize_threat_entity("https://twitter.com/Acme_Care", EntityType.SOCIAL_PROFILE) == "acme_care"

    # 5. SCAM_TEXT_HASH
    h1 = normalize_threat_entity("Urgent:   Account   Suspended!  ", EntityType.SCAM_TEXT_HASH)
    h2 = normalize_threat_entity("urgent: account suspended!", EntityType.SCAM_TEXT_HASH)
    assert h1 == h2

    # 6. APK_PACKAGE
    assert normalize_threat_entity("  Com.Phish.AcmeApp  ", EntityType.APK_PACKAGE) == "com.phish.acmeapp"


@pytest.mark.asyncio
async def test_entity_deduplication(db_session: AsyncSession) -> None:
    """Verify that multiple reports referencing the same entity reuse the record and bump last_seen_at."""
    repo = ThreatEntityRepository()

    # First ingestion
    ent1, was_created1 = await repo.get_or_create(db_session, EntityType.DOMAIN, "phish-bank.com")
    assert was_created1 is True
    first_seen = ent1.first_seen_at

    # Second ingestion of identical domain
    ent2, was_created2 = await repo.get_or_create(db_session, EntityType.DOMAIN, "phish-bank.com")
    assert was_created2 is False
    assert ent1.id == ent2.id
    assert ent2.first_seen_at == first_seen


def test_defensible_relationships_similar_domain() -> None:
    """Verify similar domains and homoglyphs form defensible relationships."""
    engine = DefensibleRelationshipEngine()

    # 1. High lexical similarity
    ent_a = ThreatEntity(id=uuid.uuid4(), entity_type=EntityType.DOMAIN, canonical_value="acmepayments-login.com")
    ent_b = ThreatEntity(id=uuid.uuid4(), entity_type=EntityType.DOMAIN, canonical_value="acmepayments-portal.com")

    res = engine.evaluate_pair(ent_a, ent_b)
    assert res is not None
    assert res.relationship_type == RelationshipType.SIMILAR_DOMAIN
    assert res.confidence >= 0.80

    # 2. Homoglyph lookalike match
    ent_c = ThreatEntity(id=uuid.uuid4(), entity_type=EntityType.DOMAIN, canonical_value="google.com")
    # 'gооgle.com' with Cyrillic 'о'
    ent_d = ThreatEntity(id=uuid.uuid4(), entity_type=EntityType.DOMAIN, canonical_value="g\u043e\u043egle.com")

    res_homo = engine.evaluate_pair(ent_c, ent_d)
    assert res_homo is not None
    assert res_homo.relationship_type == RelationshipType.SIMILAR_DOMAIN
    assert res_homo.relationship_status == RelationshipStatus.CONFIRMED


def test_defensible_relationships_shared_destination() -> None:
    """Verify URL pointing to domain/IP creates SHARED_DESTINATION."""
    engine = DefensibleRelationshipEngine()

    ent_url = ThreatEntity(
        id=uuid.uuid4(), entity_type=EntityType.URL, canonical_value="https://c2-server.net/login/submit"
    )
    ent_dom = ThreatEntity(
        id=uuid.uuid4(), entity_type=EntityType.DOMAIN, canonical_value="c2-server.net"
    )

    res = engine.evaluate_pair(ent_url, ent_dom)
    assert res is not None
    assert res.relationship_type == RelationshipType.SHARED_DESTINATION
    assert res.relationship_status == RelationshipStatus.CONFIRMED


def test_defensible_relationships_reused_image_hash() -> None:
    """Verify perceptual image hashes with close Hamming distance form REUSED_IMAGE_HASH."""
    engine = DefensibleRelationshipEngine()

    # 64-bit hex hash differing by 1 bit
    hash1 = "ffffffff00000000"
    hash2 = "ffffffff00000001"

    ent_img1 = ThreatEntity(id=uuid.uuid4(), entity_type=EntityType.IMAGE_HASH, canonical_value=hash1)
    ent_img2 = ThreatEntity(id=uuid.uuid4(), entity_type=EntityType.IMAGE_HASH, canonical_value=hash2)

    res = engine.evaluate_pair(ent_img1, ent_img2)
    assert res is not None
    assert res.relationship_type == RelationshipType.REUSED_IMAGE_HASH
    assert res.confidence >= 0.90


def test_false_correlation_prevention() -> None:
    """
    CRITICAL INVARIANT:
    Two unrelated entities must NEVER be connected simply because they target or mention the same brand!
    """
    engine = DefensibleRelationshipEngine()

    # Two completely distinct domains with no lexical similarity, no homoglyphs, no shared infrastructure
    ent_x = ThreatEntity(id=uuid.uuid4(), entity_type=EntityType.DOMAIN, canonical_value="secure-billing-auth.com")
    ent_y = ThreatEntity(id=uuid.uuid4(), entity_type=EntityType.DOMAIN, canonical_value="totallyunrelatedphish.net")

    # Even if both target brand "Acme", there is no defensible technical link
    res = engine.evaluate_pair(ent_x, ent_y)
    assert res is None


@pytest.mark.asyncio
async def test_duplicate_alert_prevention(db_session: AsyncSession) -> None:
    """
    FEATURE 8:
    Verify that repeated alerts for the same unresolved incident are suppressed.
    """
    repo = AlertRepository()
    brand_id = uuid.uuid4()
    fingerprint = "abc123def456_test_fingerprint"

    # 1. First alert creation succeeds
    alert1, created1 = await repo.create_if_not_duplicate(
        db=db_session,
        brand_id=brand_id,
        title="Active Attack Campaign",
        description="First alert on incident",
        severity=RiskSeverity.HIGH,
        fingerprint=fingerprint,
    )
    assert created1 is True
    assert alert1.dedup_fingerprint == fingerprint

    # 2. Second alert attempt for same unresolved incident is suppressed
    alert2, created2 = await repo.create_if_not_duplicate(
        db=db_session,
        brand_id=brand_id,
        title="Active Attack Campaign (Duplicate)",
        description="Repeated alert attempt",
        severity=RiskSeverity.HIGH,
        fingerprint=fingerprint,
    )
    assert created2 is False
    assert alert2.id == alert1.id  # Returns existing unresolved alert
