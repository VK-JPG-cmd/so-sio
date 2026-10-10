from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.alert import Alert
from app.models.campaign import Campaign
from app.models.campaign_membership import CampaignMembership
from app.models.entity_relationship import EntityRelationship
from app.models.enums import AlertStatus, CampaignStatus, EntityType, RelationshipStatus, RelationshipType, RiskSeverity
from app.models.threat_entity import ThreatEntity


class ThreatEntityRepository:
    """Repository for managing canonical, deduplicated threat entities."""

    async def get_by_canonical(
        self,
        db: AsyncSession,
        entity_type: EntityType,
        canonical_value: str,
    ) -> Optional[ThreatEntity]:
        """Lookup entity by its unique (entity_type, canonical_value) pair."""
        stmt = select(ThreatEntity).where(
            ThreatEntity.entity_type == entity_type,
            ThreatEntity.canonical_value == canonical_value,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        db: AsyncSession,
        entity_type: EntityType,
        canonical_value: str,
    ) -> Tuple[ThreatEntity, bool]:
        """
        Deduplicate and get or create an entity.
        If existing entity found, update last_seen_at and return (entity, False).
        If new entity, insert and return (entity, True).
        """
        existing = await self.get_by_canonical(db, entity_type, canonical_value)
        if existing:
            existing.last_seen_at = datetime.now(timezone.utc)
            await db.flush()
            return existing, False

        new_entity = ThreatEntity(
            id=uuid.uuid4(),
            entity_type=entity_type,
            canonical_value=canonical_value,
            first_seen_at=datetime.now(timezone.utc),
            last_seen_at=datetime.now(timezone.utc),
        )
        db.add(new_entity)
        await db.flush()
        await db.refresh(new_entity)
        return new_entity, True

    async def get_by_id(
        self,
        db: AsyncSession,
        entity_id: uuid.UUID,
    ) -> Optional[ThreatEntity]:
        """Fetch threat entity by UUID."""
        stmt = select(ThreatEntity).where(ThreatEntity.id == entity_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


class EntityRelationshipRepository:
    """Repository for managing evidence-backed relationships between entities."""

    async def get_relationship(
        self,
        db: AsyncSession,
        source_id: uuid.UUID,
        target_id: uuid.UUID,
        relationship_type: RelationshipType,
    ) -> Optional[EntityRelationship]:
        """Find an existing relationship between two entities."""
        stmt = select(EntityRelationship).where(
            EntityRelationship.source_entity_id == source_id,
            EntityRelationship.target_entity_id == target_id,
            EntityRelationship.relationship_type == relationship_type,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_or_update(
        self,
        db: AsyncSession,
        source_id: uuid.UUID,
        target_id: uuid.UUID,
        relationship_type: RelationshipType,
        relationship_status: RelationshipStatus = RelationshipStatus.CANDIDATE,
        evidence_id: Optional[uuid.UUID] = None,
        confidence: Optional[float] = None,
        evidence_details: Optional[Dict[str, Any]] = None,
    ) -> EntityRelationship:
        """Create or update an entity relationship with supporting evidence."""
        existing = await self.get_relationship(db, source_id, target_id, relationship_type)
        if existing:
            existing.relationship_status = relationship_status
            if confidence is not None:
                existing.confidence = confidence
            if evidence_id is not None:
                existing.evidence_id = evidence_id
            if evidence_details is not None:
                existing.evidence_details = evidence_details
            await db.flush()
            return existing

        rel = EntityRelationship(
            id=uuid.uuid4(),
            source_entity_id=source_id,
            target_entity_id=target_id,
            relationship_type=relationship_type,
            relationship_status=relationship_status,
            evidence_id=evidence_id,
            confidence=confidence,
            evidence_details=evidence_details,
        )
        db.add(rel)
        await db.flush()
        await db.refresh(rel)
        return rel

    async def list_for_entities(
        self,
        db: AsyncSession,
        entity_ids: List[uuid.UUID],
    ) -> List[EntityRelationship]:
        """Fetch all relationships where either source or target is in entity_ids."""
        if not entity_ids:
            return []
        stmt = (
            select(EntityRelationship)
            .options(
                selectinload(EntityRelationship.source_entity),
                selectinload(EntityRelationship.target_entity),
            )
            .where(
                or_(
                    EntityRelationship.source_entity_id.in_(entity_ids),
                    EntityRelationship.target_entity_id.in_(entity_ids),
                )
            )
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())


class CampaignRepository:
    """Repository for threat campaigns and membership associations."""

    async def create(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        title: str,
        risk_score: float = 0.0,
        status: CampaignStatus = CampaignStatus.ACTIVE,
        description: Optional[str] = None,
    ) -> Campaign:
        """Create a new threat campaign cluster."""
        campaign = Campaign(
            id=uuid.uuid4(),
            brand_id=brand_id,
            title=title,
            risk_score=risk_score,
            status=status,
            description=description,
        )
        db.add(campaign)
        await db.flush()
        await db.refresh(campaign)
        return campaign

    async def get_by_id(
        self,
        db: AsyncSession,
        campaign_id: uuid.UUID,
    ) -> Optional[Campaign]:
        """Fetch campaign with member associations."""
        stmt = (
            select(Campaign)
            .options(
                selectinload(Campaign.memberships).selectinload(CampaignMembership.entity),
                selectinload(Campaign.alerts),
            )
            .where(Campaign.id == campaign_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_brand(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Campaign]:
        """List campaigns for a brand."""
        stmt = (
            select(Campaign)
            .options(
                selectinload(Campaign.memberships).selectinload(CampaignMembership.entity),
                selectinload(Campaign.alerts),
            )
            .where(Campaign.brand_id == brand_id)
            .order_by(desc(Campaign.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def find_active_campaign_for_entities(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        entity_ids: List[uuid.UUID],
    ) -> Optional[Campaign]:
        """Find an existing active campaign for this brand that contains any of the given entities."""
        if not entity_ids:
            return None
        stmt = (
            select(Campaign)
            .join(CampaignMembership, CampaignMembership.campaign_id == Campaign.id)
            .where(
                Campaign.brand_id == brand_id,
                Campaign.status == CampaignStatus.ACTIVE,
                CampaignMembership.entity_id.in_(entity_ids),
            )
            .options(
                selectinload(Campaign.memberships).selectinload(CampaignMembership.entity),
                selectinload(Campaign.alerts),
            )
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def add_membership(
        self,
        db: AsyncSession,
        campaign_id: uuid.UUID,
        entity_id: uuid.UUID,
        relationship_reason: str,
    ) -> CampaignMembership:
        """Add an entity to a campaign if not already associated."""
        stmt = select(CampaignMembership).where(
            CampaignMembership.campaign_id == campaign_id,
            CampaignMembership.entity_id == entity_id,
        )
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            return existing

        membership = CampaignMembership(
            id=uuid.uuid4(),
            campaign_id=campaign_id,
            entity_id=entity_id,
            relationship_reason=relationship_reason,
        )
        db.add(membership)
        await db.flush()
        camp = await db.get(Campaign, campaign_id)
        if camp and "memberships" in camp.__dict__ and isinstance(camp.memberships, list):
            camp.memberships.append(membership)
        await db.refresh(membership)
        return membership


class AlertRepository:
    """Repository for actionable brand alerts with duplicate prevention."""

    async def get_unresolved_alert_by_fingerprint(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        fingerprint: str,
    ) -> Optional[Alert]:
        """Check for existing unresolved (OPEN or ACKNOWLEDGED) alert with identical fingerprint."""
        stmt = select(Alert).where(
            Alert.brand_id == brand_id,
            Alert.dedup_fingerprint == fingerprint,
            Alert.status.in_([AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED]),
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_if_not_duplicate(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        title: str,
        description: str,
        severity: RiskSeverity,
        fingerprint: str,
        campaign_id: Optional[uuid.UUID] = None,
    ) -> Tuple[Alert, bool]:
        """
        Creates alert only if an unresolved alert with the same fingerprint does not already exist.
        Returns (alert, was_created).
        """
        existing = await self.get_unresolved_alert_by_fingerprint(db, brand_id, fingerprint)
        if existing:
            return existing, False

        alert = Alert(
            id=uuid.uuid4(),
            brand_id=brand_id,
            campaign_id=campaign_id,
            title=title,
            description=description,
            severity=severity,
            status=AlertStatus.OPEN,
            dedup_fingerprint=fingerprint,
        )
        db.add(alert)
        await db.flush()
        await db.refresh(alert)
        return alert, True

    async def list_by_brand(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        status: Optional[AlertStatus] = None,
        severity: Optional[RiskSeverity] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Alert]:
        """List alerts for a brand with optional filtering."""
        query = select(Alert).where(Alert.brand_id == brand_id)
        if status:
            query = query.where(Alert.status == status)
        if severity:
            query = query.where(Alert.severity == severity)
        query = query.order_by(desc(Alert.created_at)).offset(offset).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(
        self,
        db: AsyncSession,
        alert_id: uuid.UUID,
    ) -> Optional[Alert]:
        """Fetch alert by id."""
        stmt = select(Alert).where(Alert.id == alert_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(
        self,
        db: AsyncSession,
        alert: Alert,
        new_status: AlertStatus,
    ) -> Alert:
        """Update incident resolution status of an alert."""
        alert.status = new_status
        await db.flush()
        await db.refresh(alert)
        return alert
