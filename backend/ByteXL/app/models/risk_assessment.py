from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional
import uuid
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, JSON, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import RiskSeverity

if TYPE_CHECKING:
    from app.models.threat_report import ThreatReport


class RiskAssessment(Base):
    """
    Unified, explainable threat risk assessment record.
    Stores deterministic scoring outputs, contributing signals,
    unavailable signals, model version, and actionable recommendations.
    """

    __tablename__ = "risk_assessments"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    report_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("threat_reports.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    entity_id: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        index=True,
    )
    model_version: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    risk_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    severity: Mapped[RiskSeverity] = mapped_column(
        Enum(RiskSeverity, name="risk_severity_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    explanation_json: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    indicators_json: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    recommendation_json: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    report: Mapped[Optional["ThreatReport"]] = relationship(
        "ThreatReport",
        back_populates="assessments",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_risk_assessments_report_created", "report_id", "created_at"),
    )
