from typing import List, Optional
import uuid
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.enums import EvidenceType, TargetType, ThreatReportStatus
from app.models.evidence import Evidence
from app.models.threat_report import ThreatReport


class ThreatReportRepository:
    """Data access repository for ThreatReport and Evidence entities."""

    async def create(
        self,
        db: AsyncSession,
        reporter_id: uuid.UUID,
        target_type: TargetType,
        target_value: str,
        description: str,
        brand_id: Optional[uuid.UUID] = None,
        status: ThreatReportStatus = ThreatReportStatus.SUBMITTED,
    ) -> ThreatReport:
        """Create and persist a new threat report."""
        report = ThreatReport(
            id=uuid.uuid4(),
            reporter_id=reporter_id,
            brand_id=brand_id,
            target_type=target_type,
            target_value=target_value,
            description=description,
            status=status,
        )
        db.add(report)
        await db.flush()
        await db.refresh(report)
        return report

    async def get_by_id(
        self,
        db: AsyncSession,
        report_id: uuid.UUID,
    ) -> Optional[ThreatReport]:
        """Fetch threat report with eagerly loaded evidences and reporter."""
        stmt = (
            select(ThreatReport)
            .options(
                selectinload(ThreatReport.evidences),
                selectinload(ThreatReport.reporter),
                selectinload(ThreatReport.brand),
            )
            .where(ThreatReport.id == report_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_reporter(
        self,
        db: AsyncSession,
        reporter_id: uuid.UUID,
        status: Optional[ThreatReportStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ThreatReport]:
        """Fetch threat reports submitted by a specific user with pagination."""
        stmt = (
            select(ThreatReport)
            .options(selectinload(ThreatReport.evidences))
            .where(ThreatReport.reporter_id == reporter_id)
        )
        if status is not None:
            stmt = stmt.where(ThreatReport.status == status)
        stmt = stmt.order_by(desc(ThreatReport.created_at)).offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def count_by_reporter(
        self,
        db: AsyncSession,
        reporter_id: uuid.UUID,
        status: Optional[ThreatReportStatus] = None,
    ) -> int:
        """Count total threat reports submitted by a specific user."""
        stmt = select(func.count(ThreatReport.id)).where(ThreatReport.reporter_id == reporter_id)
        if status is not None:
            stmt = stmt.where(ThreatReport.status == status)
        result = await db.execute(stmt)
        return result.scalar() or 0

    async def update(
        self,
        db: AsyncSession,
        report: ThreatReport,
    ) -> ThreatReport:
        """Persist modifications to a threat report."""
        await db.flush()
        await db.refresh(report)
        return report

    async def add_evidence(
        self,
        db: AsyncSession,
        report_id: uuid.UUID,
        evidence_type: EvidenceType,
        storage_key: str,
        sha256: str,
        original_filename: str,
        file_size: int,
    ) -> Evidence:
        """Create and persist an evidence artifact attachment."""
        evidence = Evidence(
            id=uuid.uuid4(),
            report_id=report_id,
            evidence_type=evidence_type,
            storage_key=storage_key,
            sha256=sha256,
            original_filename=original_filename,
            file_size=file_size,
        )
        db.add(evidence)
        await db.flush()
        await db.refresh(evidence)
        return evidence

    async def get_brand_reports(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        limit: int = 500,
        offset: int = 0,
    ) -> List[ThreatReport]:
        """Fetch threat reports targeting a specific brand, for entity ingestion."""
        stmt = (
            select(ThreatReport)
            .where(ThreatReport.brand_id == brand_id)
            .order_by(desc(ThreatReport.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_evidence_by_id(
        self,
        db: AsyncSession,
        evidence_id: uuid.UUID,
    ) -> Optional[Evidence]:
        """Fetch an evidence attachment by UUID."""
        stmt = select(Evidence).where(Evidence.id == evidence_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
