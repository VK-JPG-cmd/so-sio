"""
Repository for Discovered Indicators and Discovery Checkpoints.
Provides persistence, idempotent deduplication, and operational health metrics.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import uuid
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.discovered_indicator import DiscoveredIndicator
from app.models.discovery_checkpoint import DiscoveryCheckpoint
from app.services.discovery.connector import DiscoveredIndicatorRecord


class DiscoveredIndicatorRepository:
    """Repository for external threat indicator observations."""

    async def get_by_source_and_canonical(
        self,
        db: AsyncSession,
        source_id: str,
        canonical_value: str,
    ) -> Optional[DiscoveredIndicator]:
        """Lookup observation by stable source and canonical identifier."""
        stmt = select(DiscoveredIndicator).where(
            DiscoveredIndicator.source_id == source_id,
            DiscoveredIndicator.canonical_value == canonical_value,
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_or_create(
        self,
        db: AsyncSession,
        record: DiscoveredIndicatorRecord,
    ) -> Tuple[DiscoveredIndicator, bool]:
        """
        Idempotent observation ingestion.
        If already observed from this source, bumps last_observed_at without creating duplicates.
        Returns (indicator, was_created).
        """
        existing = await self.get_by_source_and_canonical(
            db, record.source_id, record.canonical_value
        )
        if existing:
            existing.last_observed_at = datetime.now(timezone.utc)
            if record.source_last_seen_at:
                existing.source_last_seen_at = record.source_last_seen_at
            await db.flush()
            return existing, False

        indicator = DiscoveredIndicator(
            id=uuid.uuid4(),
            source_id=record.source_id,
            source_record_id=record.source_record_id,
            indicator_type=record.indicator_type,
            raw_indicator=record.raw_indicator,
            canonical_value=record.canonical_value,
            source_first_seen_at=record.source_first_seen_at,
            source_last_seen_at=record.source_last_seen_at,
            ingested_at=datetime.now(timezone.utc),
            last_observed_at=datetime.now(timezone.utc),
            processing_status="PENDING",
            evidence_payload={"tags": record.tags, **record.raw_payload},
        )
        db.add(indicator)
        await db.flush()
        await db.refresh(indicator)
        return indicator, True

    async def update(
        self,
        db: AsyncSession,
        indicator: DiscoveredIndicator,
    ) -> DiscoveredIndicator:
        """Persist analysis and correlation results for an indicator."""
        await db.flush()
        await db.refresh(indicator)
        return indicator

    async def list_recent(
        self,
        db: AsyncSession,
        source_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[DiscoveredIndicator]:
        """Query recent indicators with optional filtering."""
        query = select(DiscoveredIndicator)
        if source_id:
            query = query.where(DiscoveredIndicator.source_id == source_id)
        if status:
            query = query.where(DiscoveredIndicator.processing_status == status)
        query = query.order_by(desc(DiscoveredIndicator.ingested_at)).offset(offset).limit(limit)
        res = await db.execute(query)
        return list(res.scalars().all())

    async def count_by_status(self, db: AsyncSession) -> Dict[str, int]:
        """Aggregate counts of discovered indicators by processing status."""
        stmt = select(
            DiscoveredIndicator.processing_status, func.count(DiscoveredIndicator.id)
        ).group_by(DiscoveredIndicator.processing_status)
        res = await db.execute(stmt)
        return dict(res.all())


class DiscoveryCheckpointRepository:
    """Repository for source checkpoints and polling metrics."""

    async def get_or_create(
        self,
        db: AsyncSession,
        source_id: str,
    ) -> DiscoveryCheckpoint:
        """Fetch or initialize checkpoint record for a threat source."""
        stmt = select(DiscoveryCheckpoint).where(DiscoveryCheckpoint.source_id == source_id)
        res = await db.execute(stmt)
        cp = res.scalar_one_or_none()
        if cp:
            return cp

        cp = DiscoveryCheckpoint(
            id=uuid.uuid4(),
            source_id=source_id,
            status="IDLE",
        )
        db.add(cp)
        await db.flush()
        await db.refresh(cp)
        return cp

    async def record_poll_cycle(
        self,
        db: AsyncSession,
        source_id: str,
        success: bool,
        new_checkpoint: Optional[str] = None,
        fetched: int = 0,
        accepted: int = 0,
        rejected: int = 0,
        error_message: Optional[str] = None,
    ) -> DiscoveryCheckpoint:
        """Record the outcome and telemetry of a polling execution."""
        cp = await self.get_or_create(db, source_id)
        now = datetime.now(timezone.utc)
        cp.last_poll_at = now
        cp.poll_count += 1
        cp.indicators_fetched_total += fetched
        cp.indicators_accepted_total += accepted
        cp.indicators_rejected_total += rejected

        if success:
            cp.last_success_at = now
            cp.status = "IDLE"
            cp.last_error_message = None
            if new_checkpoint:
                cp.checkpoint_value = new_checkpoint
        else:
            cp.last_error_at = now
            cp.status = "ERROR"
            cp.last_error_message = error_message

        await db.flush()
        await db.refresh(cp)
        return cp

    async def list_all(self, db: AsyncSession) -> List[DiscoveryCheckpoint]:
        """Fetch all source checkpoints."""
        stmt = select(DiscoveryCheckpoint).order_by(DiscoveryCheckpoint.source_id)
        res = await db.execute(stmt)
        return list(res.scalars().all())
