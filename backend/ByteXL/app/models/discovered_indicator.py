from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional
import uuid
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, JSON, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import EntityType

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.brand import Brand
    from app.models.campaign import Campaign
    from app.models.threat_entity import ThreatEntity


class DiscoveredIndicator(Base):
    """
    Threat observation ingested from authorized external threat intelligence feeds
    or discovery connectors (e.g., URLhaus).
    Tracks provenance, brand matching, and downstream risk assessment/campaign correlation.
    """

    __tablename__ = "discovered_indicators"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    source_record_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    indicator_type: Mapped[EntityType] = mapped_column(
        Enum(EntityType, name="entity_type_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    raw_indicator: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )
    canonical_value: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
        index=True,
    )

    # Timestamps
    source_first_seen_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    source_last_seen_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    last_observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Processing Lifecycle: PENDING, ANALYZED, NO_BRAND_MATCH, FAILED
    processing_status: Mapped[str] = mapped_column(
        String(32),
        default="PENDING",
        nullable=False,
        index=True,
    )

    # Associated Brand (only populated when defensible brand evidence exists)
    brand_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("brands.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Risk Evaluation Outcome
    risk_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    risk_level: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
    )

    # Downstream Correlation Associations
    threat_entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("threat_entities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    campaign_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    alert_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("alerts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Evidence details & error diagnostics
    evidence_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    brand: Mapped[Optional["Brand"]] = relationship(
        "Brand",
        lazy="selectin",
    )
    threat_entity: Mapped[Optional["ThreatEntity"]] = relationship(
        "ThreatEntity",
        lazy="selectin",
    )
    campaign: Mapped[Optional["Campaign"]] = relationship(
        "Campaign",
        lazy="selectin",
    )
    alert: Mapped[Optional["Alert"]] = relationship(
        "Alert",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("source_id", "canonical_value", name="uq_discovered_indicator_source_canonical"),
        Index("ix_discovered_indicators_source_status", "source_id", "processing_status"),
        Index("ix_discovered_indicators_source_record", "source_id", "source_record_id"),
    )
