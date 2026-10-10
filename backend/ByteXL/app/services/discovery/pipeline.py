"""
Threat Discovery Processing Pipeline.
Processes discovered indicators safely:
1. Normalizes and validates syntax
2. Enforces idempotent deduplication across observation cycles
3. Assesses evidence against registered verified brands
4. Preserves official brand assets (zero false-positive protection)
5. Executes domain/URL detection and risk scoring
6. Integrates qualifying observations into Campaign Correlation
7. Generates deduplicated alerts via AlertRepository
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import get_logger
from app.models.discovered_indicator import DiscoveredIndicator
from app.models.enums import EntityType
from app.repositories.correlation_repo import ThreatEntityRepository
from app.repositories.discovery_repo import DiscoveredIndicatorRepository
from app.services.correlation.campaign_service import CampaignCorrelationService
from app.services.detection.brand_intelligence import BrandIntelligenceService
from app.services.detection.domain_analysis import DomainAnalysisService
from app.services.discovery.connector import DiscoveredIndicatorRecord

logger = get_logger("app.services.discovery.pipeline")


class ThreatDiscoveryPipeline:
    """
    Unified ingestion and processing engine for discovered external threat observations.
    """

    def __init__(self) -> None:
        self.indicator_repo = DiscoveredIndicatorRepository()
        self.brand_intel = BrandIntelligenceService()
        self.domain_service = DomainAnalysisService()
        self.correlation_service = CampaignCorrelationService()
        self.entity_repo = ThreatEntityRepository()

    async def process_record(
        self,
        db: AsyncSession,
        record: DiscoveredIndicatorRecord,
    ) -> DiscoveredIndicator:
        """
        Process a single observation record end-to-end.
        Idempotent: Repeated observations update last_observed_at without
        duplicating downstream entities or alerts.
        """
        # 1. Deduplicate & persist observation
        indicator, was_created = await self.indicator_repo.get_or_create(db, record)

        if not was_created:
            # Observation already indexed; updated timestamp, skip duplicate processing
            logger.info(
                f"Repeated observation for {record.source_id}:{record.canonical_value}. "
                "Updated last_observed_at, skipping duplicate alert generation."
            )
            return indicator

        # 2. Extract target hostname/domain for brand correlation
        target_host = self._extract_target_host(record.canonical_value, record.indicator_type)
        if not target_host:
            indicator.processing_status = "INVALID_SYNTAX"
            indicator.processed_at = datetime.now(timezone.utc)
            await self.indicator_repo.update(db, indicator)
            return indicator

        # 3. Retrieve verified brands
        verified_brands = await self.brand_intel.list_all_verified_brands(db)
        if not verified_brands:
            indicator.processing_status = "NO_BRAND_MATCH"
            indicator.processed_at = datetime.now(timezone.utc)
            await self.indicator_repo.update(db, indicator)
            return indicator

        # 4. Analyze target against verified brand intelligence
        domain_result = self.domain_service.analyze_domain(target_host, verified_brands)

        # 5. Check if it's the brand's official domain (False-positive protection)
        if domain_result.is_official_domain:
            indicator.processing_status = "OFFICIAL_BRAND_ASSET"
            indicator.risk_score = 0.0
            indicator.risk_level = "BENIGN"
            indicator.processed_at = datetime.now(timezone.utc)
            await self.indicator_repo.update(db, indicator)
            logger.info(
                f"Discovered indicator {record.canonical_value} matched official domain for "
                f"{domain_result.matched_brand_name}. Exempted from threat alerting."
            )
            return indicator

        # 6. Verify whether supporting evidence associates the indicator with a brand
        matched_brand_id = domain_result.matched_brand_id
        is_evidence_backed = (
            matched_brand_id is not None
            and (
                domain_result.similarity_score >= 70.0
                or domain_result.has_homoglyphs
                or bool(domain_result.suspicious_keywords_found)
                or domain_result.threat_intel_match
            )
        )

        if not is_evidence_backed or not matched_brand_id:
            # General internet threat with no defensible connection to our registered brands
            indicator.processing_status = "NO_BRAND_MATCH"
            indicator.risk_score = domain_result.risk_score
            indicator.risk_level = domain_result.risk_level
            indicator.processed_at = datetime.now(timezone.utc)
            await self.indicator_repo.update(db, indicator)
            return indicator

        # 7. Brand matched with supporting evidence: attach brand and risk score
        brand_uuid = uuid.UUID(matched_brand_id)
        indicator.brand_id = brand_uuid
        indicator.risk_score = domain_result.risk_score
        indicator.risk_level = domain_result.risk_level
        indicator.processing_status = "MATCHED_BRAND"

        # 8. Ingest canonical threat entity
        threat_ent, _ = await self.entity_repo.get_or_create(
            db, record.indicator_type, record.canonical_value
        )
        indicator.threat_entity_id = threat_ent.id

        # Also register domain entity if observation was a URL
        if record.indicator_type == EntityType.URL:
            await self.entity_repo.get_or_create(db, EntityType.DOMAIN, target_host)

        # 9. Trigger Campaign Correlation & Deduplicated Alerting
        try:
            corr_summary = await self.correlation_service.run_brand_correlation(db, brand_uuid)
            logger.info(
                f"Campaign correlation executed for brand {brand_uuid}: "
                f"{corr_summary.get('campaigns_created')} campaign(s), "
                f"{corr_summary.get('alerts_created')} alert(s)."
            )

            # Retrieve any active campaign containing this entity
            campaigns = await self.correlation_service.campaign_repo.find_active_campaign_for_entities(
                db, brand_uuid, [threat_ent.id]
            )
            if campaigns:
                indicator.campaign_id = campaigns.id
                if campaigns.alerts:
                    indicator.alert_id = campaigns.alerts[0].id

        except Exception as exc:
            logger.error(f"Error executing correlation during discovery processing: {exc}", exc_info=True)
            indicator.error_message = str(exc)

        indicator.processed_at = datetime.now(timezone.utc)
        await self.indicator_repo.update(db, indicator)
        return indicator

    def _extract_target_host(self, canonical_value: str, entity_type: EntityType) -> Optional[str]:
        """Extract clean hostname from URL, Domain, or IP address."""
        if entity_type == EntityType.URL or "://" in canonical_value:
            try:
                parsed = urlparse(canonical_value)
                return (parsed.hostname or "").lower()
            except Exception:
                return None
        elif entity_type in (EntityType.DOMAIN, EntityType.IP_ADDRESS):
            return canonical_value.split("/")[0].split(":")[0].strip().lower()
        return None
