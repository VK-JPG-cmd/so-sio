from pathlib import Path
from typing import List, Optional, Tuple
import uuid
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import (
    AuthorizationError,
    NotFoundError,
    ValidationError,
)
from app.core.file_security import FileSecurityService
from app.core.logging import get_logger
from app.models.enums import EvidenceType, ThreatReportStatus, UserRole
from app.models.evidence import Evidence
from app.models.threat_report import ThreatReport
from app.models.user import User
from app.repositories.brand_repo import BrandRepository
from app.repositories.threat_report_repo import ThreatReportRepository
from app.schemas.threat_report import ThreatReportCreate

from app.repositories.audit_repo import AuditLogRepository

logger = get_logger("app.services.threat_report_service")


class ThreatReportService:
    """
    Business logic for customer threat reporting, report access control,
    investigation status lifecycle, and secure evidence storage.
    """

    def __init__(self) -> None:
        self.report_repo = ThreatReportRepository()
        self.brand_repo = BrandRepository()
        self.file_security = FileSecurityService()
        self.audit_repo = AuditLogRepository()
        self._correlation_service = None

    @property
    def correlation_service(self):
        """Lazy import to avoid circular dependency at module load time."""
        if self._correlation_service is None:
            from app.services.correlation.campaign_service import CampaignCorrelationService
            self._correlation_service = CampaignCorrelationService()
        return self._correlation_service

    async def create_report(
        self,
        db: AsyncSession,
        current_user: User,
        payload: ThreatReportCreate,
    ) -> ThreatReport:
        """
        Create a new digital threat report.
        Strictly enforces that only customers (or admins) may submit reports.
        """
        if current_user.role != UserRole.CUSTOMER and current_user.role != UserRole.ADMIN:
            raise AuthorizationError("Only customers may submit threat reports.")

        # If brand ID is provided, verify it exists
        if payload.brand_id:
            brand = await self.brand_repo.get_by_id(db, payload.brand_id)
            if not brand:
                raise NotFoundError(f"Referenced brand '{payload.brand_id}' not found.")

        report = await self.report_repo.create(
            db=db,
            reporter_id=current_user.id,
            target_type=payload.target_type,
            target_value=payload.target_value,
            description=payload.description,
            brand_id=payload.brand_id,
            status=ThreatReportStatus.SUBMITTED,
        )

        # Auto-ingest the threat entity into the correlation index (best-effort).
        # Runs inside the same transaction so failure rolls back cleanly.
        try:
            await self.correlation_service.ingest_report_entity(db, report)
        except Exception as exc:  # pragma: no cover
            logger.warning(
                f"Entity ingestion skipped for report {report.id}: {exc}"
            )

        await db.commit()
        logger.info(
            f"Threat report {report.id} created by user {current_user.id} "
            f"(target_type={report.target_type.value}, target_value={report.target_value})"
        )
        return report

    async def get_my_reports(
        self,
        db: AsyncSession,
        current_user: User,
        status: Optional[ThreatReportStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ThreatReport]:
        """
        Retrieve all reports submitted by the authenticated customer,
        optionally filtered by investigation status.
        """
        return await self.report_repo.get_by_reporter(
            db=db,
            reporter_id=current_user.id,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def count_my_reports(
        self,
        db: AsyncSession,
        current_user: User,
        status: Optional[ThreatReportStatus] = None,
    ) -> int:
        """Count total reports submitted by the authenticated customer."""
        return await self.report_repo.count_by_reporter(
            db=db,
            reporter_id=current_user.id,
            status=status,
        )

    async def get_report_by_id(
        self,
        db: AsyncSession,
        report_id: uuid.UUID,
        current_user: User,
    ) -> ThreatReport:
        """
        Retrieve threat report by ID with ownership enforcement.
        A customer can only view their own private reports.
        Admins can view all reports.
        """
        report = await self.report_repo.get_by_id(db, report_id)
        if not report:
            raise NotFoundError(f"Threat report with id '{report_id}' not found.")

        is_owner = report.reporter_id == current_user.id
        is_admin = current_user.role == UserRole.ADMIN

        if not is_owner and not is_admin:
            logger.warning(
                f"Cross-owner report access attempt: user {current_user.id} "
                f"attempted to view report {report_id} owned by {report.reporter_id}"
            )
            raise AuthorizationError("You do not have permission to access this threat report.")

        return report

    async def update_report_status(
        self,
        db: AsyncSession,
        report_id: uuid.UUID,
        current_user: User,
        new_status: ThreatReportStatus,
    ) -> ThreatReport:
        """
        Update the investigation status of a threat report (admin only).
        """
        if current_user.role != UserRole.ADMIN:
            raise AuthorizationError("Only administrators may update threat report status.")

        report = await self.report_repo.get_by_id(db, report_id)
        if not report:
            raise NotFoundError(f"Threat report with id '{report_id}' not found.")

        old_status = report.status
        report.status = new_status
        await self.report_repo.update(db, report)

        await self.audit_repo.create_log(
            db=db,
            actor_user_id=current_user.id,
            action="THREAT_REPORT_STATUS_UPDATE",
            entity_type="THREAT_REPORT",
            entity_id=str(report.id),
            details={"old_status": old_status.value, "new_status": new_status.value},
            brand_id=report.brand_id,
        )

        await db.commit()
        logger.info(f"Threat report {report_id} status updated to {new_status.value} by admin {current_user.id}")
        return report

    async def attach_evidence(
        self,
        db: AsyncSession,
        report_id: uuid.UUID,
        file: UploadFile,
        evidence_type: EvidenceType,
        current_user: User,
    ) -> Evidence:
        """
        Validate, inspect, hash, and safely store evidence for a threat report.
        Enforces ownership before accepting uploads.
        """
        report = await self.report_repo.get_by_id(db, report_id)
        if not report:
            raise NotFoundError(f"Threat report with id '{report_id}' not found.")

        is_owner = report.reporter_id == current_user.id
        is_admin = current_user.role == UserRole.ADMIN

        if not is_owner and not is_admin:
            raise AuthorizationError("You do not have permission to attach evidence to this report.")

        # Process and store file through security pipeline
        storage_key, sha256_hex, original_filename, file_size = (
            await self.file_security.process_and_store_file(file, report_id)
        )

        evidence = await self.report_repo.add_evidence(
            db=db,
            report_id=report_id,
            evidence_type=evidence_type,
            storage_key=storage_key,
            sha256=sha256_hex,
            original_filename=original_filename,
            file_size=file_size,
        )
        await db.commit()
        return evidence

    async def get_evidence_file(
        self,
        db: AsyncSession,
        report_id: uuid.UUID,
        evidence_id: uuid.UUID,
        current_user: User,
    ) -> Tuple[Path, Evidence]:
        """
        Retrieve secure evidence file path after enforcing authorization boundaries.
        Returns the resolved on-disk path and evidence metadata.
        """
        report = await self.report_repo.get_by_id(db, report_id)
        if not report:
            raise NotFoundError(f"Threat report with id '{report_id}' not found.")

        is_owner = report.reporter_id == current_user.id
        is_admin = current_user.role == UserRole.ADMIN

        if not is_owner and not is_admin:
            logger.warning(
                f"Unauthorized evidence access attempt: user {current_user.id} "
                f"attempted to download evidence {evidence_id} from report {report_id}"
            )
            raise AuthorizationError("You do not have permission to access this evidence.")

        evidence = await self.report_repo.get_evidence_by_id(db, evidence_id)
        if not evidence or evidence.report_id != report_id:
            raise NotFoundError(f"Evidence with id '{evidence_id}' not found on this report.")

        file_path = self.file_security.get_secure_file_path(evidence.storage_key)
        return file_path, evidence
