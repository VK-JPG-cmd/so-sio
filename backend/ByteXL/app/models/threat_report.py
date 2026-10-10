from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
import uuid
from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import TargetType, ThreatReportStatus

if TYPE_CHECKING:
    from app.models.brand import Brand
    from app.models.evidence import Evidence
    from app.models.risk_assessment import RiskAssessment
    from app.models.user import User


class ThreatReport(Base):
    """Customer-submitted threat, scam, impersonation, or malicious digital activity report."""

    __tablename__ = "threat_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    reporter_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    brand_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("brands.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    target_type: Mapped[TargetType] = mapped_column(
        Enum(TargetType, name="target_type_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    target_value: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    status: Mapped[ThreatReportStatus] = mapped_column(
        Enum(ThreatReportStatus, name="threat_report_status_enum", native_enum=False),
        default=ThreatReportStatus.SUBMITTED,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    reporter: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
    )
    brand: Mapped[Optional["Brand"]] = relationship(
        "Brand",
        lazy="selectin",
    )
    evidences: Mapped[List["Evidence"]] = relationship(
        "Evidence",
        back_populates="report",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    assessments: Mapped[List["RiskAssessment"]] = relationship(
        "RiskAssessment",
        back_populates="report",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(RiskAssessment.created_at)",
    )

    __table_args__ = (
        Index("ix_threat_reports_reporter_created", "reporter_id", "created_at"),
        Index("ix_threat_reports_status_target", "status", "target_type"),
    )
