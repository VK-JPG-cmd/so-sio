"""
Threat Intelligence and Campaign Correlation Service.
Groups related entities into candidate campaigns, creates alerts with duplicate prevention,
and generates correlation graph representations.
"""

from collections import defaultdict
import hashlib
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AuthorizationError, NotFoundError
from app.core.logging import get_logger
from app.models.alert import Alert
from app.models.brand import Brand
from app.models.campaign import Campaign
from app.models.campaign_membership import CampaignMembership
from app.models.entity_relationship import EntityRelationship
from app.models.enums import AlertStatus, CampaignStatus, EntityType, RelationshipStatus, RiskSeverity, TargetType, UserRole
from app.models.threat_entity import ThreatEntity
from app.models.threat_report import ThreatReport
from app.repositories.correlation_repo import (
    AlertRepository,
    CampaignRepository,
    EntityRelationshipRepository,
    ThreatEntityRepository,
)
from app.services.correlation.normalization import normalize_threat_entity
from app.services.correlation.relationship_engine import DefensibleRelationshipEngine

logger = get_logger("app.services.correlation.campaign_service")


class CampaignCorrelationService:
    """Service orchestrating entity deduplication, relationship inference, campaigns, and alerts."""

    def __init__(self) -> None:
        self.entity_repo = ThreatEntityRepository()
        self.relationship_repo = EntityRelationshipRepository()
        self.campaign_repo = CampaignRepository()
        self.alert_repo = AlertRepository()
        self.engine = DefensibleRelationshipEngine()

    async def verify_brand_ownership(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        current_user: Any,
    ) -> Brand:
        """
        Enforce strict brand ownership authorization.
        A brand owner can access only their own brand data. Admins have global access.
        """
        stmt = select(Brand).where(Brand.id == brand_id)
        result = await db.execute(stmt)
        brand = result.scalar_one_or_none()
        if not brand:
            raise NotFoundError(f"Brand with id '{brand_id}' not found.")

        is_owner = brand.owner_user_id == current_user.id
        is_admin = current_user.role == UserRole.ADMIN

        if not is_owner and not is_admin:
            logger.warning(
                f"Unauthorized brand correlation access: user {current_user.id} tried accessing brand {brand_id}"
            )
            raise AuthorizationError("You do not have permission to access data for this brand.")

        return brand

    def map_target_type_to_entity_type(self, target_type: TargetType) -> EntityType:
        """Map report target type to canonical entity type."""
        mapping = {
            TargetType.DOMAIN: EntityType.DOMAIN,
            TargetType.URL: EntityType.URL,
            TargetType.SOCIAL_PROFILE: EntityType.SOCIAL_PROFILE,
            TargetType.SCAM_TEXT: EntityType.SCAM_TEXT_HASH,
            TargetType.MOBILE_APP: EntityType.APK_PACKAGE,
        }
        return mapping.get(target_type, EntityType.DOMAIN)

    async def ingest_report_entity(
        self,
        db: AsyncSession,
        report: ThreatReport,
    ) -> ThreatEntity:
        """Normalize, deduplicate, and persist entity from a submitted threat report."""
        entity_type = self.map_target_type_to_entity_type(report.target_type)
        canonical = normalize_threat_entity(report.target_value, entity_type)
        entity, _ = await self.entity_repo.get_or_create(db, entity_type, canonical)
        return entity

    async def correlate_entities(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        entities: List[ThreatEntity],
        evidence_id: Optional[uuid.UUID] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[EntityRelationship]:
        """
        Evaluate pairs across a list of entities and create evidence-backed relationships.
        Never connects entities solely because they target the same brand.
        """
        created_relationships: List[EntityRelationship] = []

        n = len(entities)
        for i in range(n):
            for j in range(i + 1, n):
                ent_a = entities[i]
                ent_b = entities[j]

                evaluation = self.engine.evaluate_pair(ent_a, ent_b, context)
                if evaluation:
                    rel = await self.relationship_repo.create_or_update(
                        db=db,
                        source_id=ent_a.id,
                        target_id=ent_b.id,
                        relationship_type=evaluation.relationship_type,
                        relationship_status=evaluation.relationship_status,
                        evidence_id=evidence_id,
                        confidence=evaluation.confidence,
                        evidence_details={
                            "reason": evaluation.reason,
                            **evaluation.evidence_details,
                        },
                    )
                    created_relationships.append(rel)

        return created_relationships

    async def build_campaigns_for_brand(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        entities: List[ThreatEntity],
    ) -> List[Campaign]:
        """
        Group correlated entities into candidate campaigns using connected components.
        Generates alerts for significant campaigns with duplicate prevention.
        """
        if not entities:
            return []

        entity_ids = [e.id for e in entities]
        relationships = await self.relationship_repo.list_for_entities(db, entity_ids)

        # Build adjacency graph
        adj: Dict[uuid.UUID, Set[uuid.UUID]] = defaultdict(set)
        rel_map: Dict[Tuple[uuid.UUID, uuid.UUID], EntityRelationship] = {}

        for rel in relationships:
            adj[rel.source_entity_id].add(rel.target_entity_id)
            adj[rel.target_entity_id].add(rel.source_entity_id)
            rel_map[(rel.source_entity_id, rel.target_entity_id)] = rel
            rel_map[(rel.target_entity_id, rel.source_entity_id)] = rel

        # Find connected components
        visited: Set[uuid.UUID] = set()
        components: List[List[ThreatEntity]] = []
        entity_dict = {e.id: e for e in entities}

        for ent in entities:
            if ent.id not in visited:
                comp: List[ThreatEntity] = []
                queue = [ent.id]
                visited.add(ent.id)

                while queue:
                    curr_id = queue.pop(0)
                    if curr_id in entity_dict:
                        comp.append(entity_dict[curr_id])
                    for neighbor_id in adj[curr_id]:
                        if neighbor_id not in visited:
                            visited.add(neighbor_id)
                            queue.append(neighbor_id)

                if len(comp) >= 2:  # Form campaign only if technical links connect 2+ entities
                    components.append(comp)

        created_campaigns: List[Campaign] = []
        newly_created_alerts = 0

        for comp in components:
            comp_entity_ids = [m.id for m in comp]
            existing_campaign = await self.campaign_repo.find_active_campaign_for_entities(
                db=db,
                brand_id=brand_id,
                entity_ids=comp_entity_ids,
            )

            if existing_campaign:
                campaign = existing_campaign
                for member in comp:
                    reason = "Direct technical relationship in connected cluster."
                    await self.campaign_repo.add_membership(db, campaign.id, member.id, reason)
            else:
                primary = comp[0]
                title = f"Campaign: {primary.canonical_value} Infrastructure Cluster"
                campaign = await self.campaign_repo.create(
                    db=db,
                    brand_id=brand_id,
                    title=title,
                    risk_score=75.0,  # Cluster indicates elevated risk
                    status=CampaignStatus.ACTIVE,
                    description=f"Automated threat campaign grouping {len(comp)} technically connected entities.",
                )

                for member in comp:
                    reason = "Direct technical relationship in connected cluster."
                    await self.campaign_repo.add_membership(db, campaign.id, member.id, reason)

            # Generate alert for this campaign with duplicate prevention
            alert, was_created = await self._generate_campaign_alert(db, brand_id, campaign, len(comp))
            if was_created:
                newly_created_alerts += 1
            created_campaigns.append(campaign)

        self.last_alerts_created_count = newly_created_alerts
        return created_campaigns

    async def _generate_campaign_alert(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        campaign: Campaign,
        member_count: int,
    ) -> Tuple[Optional[Alert], bool]:
        """
        Generate an alert for a threat campaign.
        Enforces Feature 8: Prevents duplicate alerts for the same unresolved incident.
        """
        # Deduplication fingerprint based on brand and campaign id
        fingerprint = hashlib.sha256(f"{brand_id}:{campaign.id}".encode("utf-8")).hexdigest()

        title = f"Correlated Threat Campaign Detected: {campaign.title}"
        description = (
            f"BrandShield AI correlated {member_count} threat entities into an active campaign "
            f"targeting your brand with risk score {campaign.risk_score:.1f}. "
            "Actionable review recommended."
        )
        severity = RiskSeverity.HIGH if campaign.risk_score >= 60.0 else RiskSeverity.MEDIUM
        if campaign.risk_score >= 80.0:
            severity = RiskSeverity.CRITICAL

        alert, was_created = await self.alert_repo.create_if_not_duplicate(
            db=db,
            brand_id=brand_id,
            title=title,
            description=description,
            severity=severity,
            fingerprint=fingerprint,
            campaign_id=campaign.id,
        )

        if was_created:
            logger.info(f"Generated new alert {alert.id} for brand {brand_id} and campaign {campaign.id}")
        else:
            logger.info(f"Duplicate alert suppressed for fingerprint {fingerprint} (unresolved alert exists)")

        return alert, was_created

    async def get_brand_graph(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Extract complete threat relationship graph for visual representation.
        Nodes include ThreatEntities and Campaigns. Edges include EntityRelationships and Memberships.
        """
        campaigns = await self.campaign_repo.list_by_brand(db, brand_id, limit=100)

        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        seen_entity_ids: Set[uuid.UUID] = set()

        camp_ids = [c.id for c in campaigns]
        for camp in campaigns:
            nodes.append({
                "id": str(camp.id),
                "label": camp.title,
                "type": "CAMPAIGN",
                "risk_score": camp.risk_score,
                "status": camp.status.value,
            })

        if camp_ids:
            mem_stmt = (
                select(CampaignMembership)
                .options(selectinload(CampaignMembership.entity))
                .where(CampaignMembership.campaign_id.in_(camp_ids))
            )
            mem_res = await db.execute(mem_stmt)
            for mem in mem_res.scalars().all():
                ent = mem.entity
                if ent and ent.id not in seen_entity_ids:
                    seen_entity_ids.add(ent.id)
                    nodes.append({
                        "id": str(ent.id),
                        "label": ent.canonical_value,
                        "type": "ENTITY",
                        "entity_type": ent.entity_type.value,
                        "first_seen_at": ent.first_seen_at.isoformat(),
                    })

                edges.append({
                    "source": str(mem.campaign_id),
                    "target": str(mem.entity_id),
                    "relationship_type": "CAMPAIGN_MEMBERSHIP",
                    "reason": mem.relationship_reason,
                })

        # Also retrieve direct relationships between entities
        if seen_entity_ids:
            relationships = await self.relationship_repo.list_for_entities(db, list(seen_entity_ids))
            for rel in relationships:
                edges.append({
                    "source": str(rel.source_entity_id),
                    "target": str(rel.target_entity_id),
                    "relationship_type": rel.relationship_type.value,
                    "status": rel.relationship_status.value,
                    "confidence": rel.confidence,
                    "details": rel.evidence_details,
                })

        return {
            "brand_id": str(brand_id),
            "disclaimer": "Graph correlations reflect evidence-backed technical connections and do not prove common criminal ownership.",
            "nodes": nodes,
            "edges": edges,
        }

    async def get_entities_for_brand(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        limit: int = 500,
    ) -> List[ThreatEntity]:
        """
        Retrieve all canonical threat entities associated with reports targeting this brand.
        Fetches brand reports, ingests any unindexed entities, and returns the full entity list.
        """
        from app.repositories.threat_report_repo import ThreatReportRepository
        report_repo = ThreatReportRepository()
        reports = await report_repo.get_brand_reports(db, brand_id, limit=limit)

        entities: List[ThreatEntity] = []
        seen_ids: set = set()

        for report in reports:
            try:
                entity = await self.ingest_report_entity(db, report)
                if entity.id not in seen_ids:
                    seen_ids.add(entity.id)
                    entities.append(entity)
            except Exception:
                pass  # Skip malformed report targets

        return entities

    async def run_brand_correlation(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Execute the full end-to-end correlation pipeline for a brand:
        1. Ingest all report entities for the brand.
        2. Evaluate all entity pairs for defensible technical relationships.
        3. Build connected-component campaigns from confirmed relationships.
        4. Generate deduplicated alerts for detected campaigns.

        Returns a summary dict with counts.
        """
        entities = await self.get_entities_for_brand(db, brand_id)

        if len(entities) < 2:
            return {
                "entities_ingested": len(entities),
                "relationships_created": 0,
                "campaigns_created": 0,
                "alerts_created": 0,
                "message": "Insufficient entities to form relationships. At least 2 distinct entities required.",
            }

        relationships = await self.correlate_entities(db, brand_id, entities)
        campaigns = await self.build_campaigns_for_brand(db, brand_id, entities)
        alerts_created = getattr(self, "last_alerts_created_count", len(campaigns))

        return {
            "entities_ingested": len(entities),
            "relationships_created": len(relationships),
            "campaigns_created": len(campaigns),
            "alerts_created": alerts_created,
            "message": f"Correlation complete: {len(campaigns)} campaign(s) detected from {len(entities)} entities.",
        }

