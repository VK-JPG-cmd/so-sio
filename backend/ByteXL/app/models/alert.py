from datetime import datetime
from typing import TYPE_CHECKING, Optional
import uuid
from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import AlertStatus, RiskSeverity

if TYPE_CHECKING:
    from app.models.brand import Brand
    from app.models.campaign import Campaign


class Alert(Base):
    """
    Actionable brand alert generated for high-risk threat incidents and correlated campaigns.
    Implements deduplication fingerprints to prevent alert flooding for unresolved incidents.
    """

    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    brand_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    campaign_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    severity: Mapped[RiskSeverity] = mapped_column(
        Enum(RiskSeverity, name="risk_severity_enum", native_enum=False),
        default=RiskSeverity.MEDIUM,
        nullable=False,
        index=True,
    )
    status: Mapped[AlertStatus] = mapped_column(
        Enum(AlertStatus, name="alert_status_enum", native_enum=False),
        default=AlertStatus.OPEN,
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    dedup_fingerprint: Mapped[str] = mapped_column(
        String(64),
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
    brand: Mapped["Brand"] = relationship(
        "Brand",
        lazy="selectin",
    )
    campaign: Mapped[Optional["Campaign"]] = relationship(
        "Campaign",
        back_populates="alerts",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_alerts_brand_fingerprint_status", "brand_id", "dedup_fingerprint", "status"),
        Index("ix_alerts_brand_created", "brand_id", "created_at"),
    )
