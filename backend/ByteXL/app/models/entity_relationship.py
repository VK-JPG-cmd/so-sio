from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional
import uuid
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, JSON, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import RelationshipStatus, RelationshipType

if TYPE_CHECKING:
    from app.models.evidence import Evidence
    from app.models.threat_entity import ThreatEntity


class EntityRelationship(Base):
    """
    Evidence-backed directional relationship between two threat entities.
    Tracks shared infrastructure, similar domains, reused hashes, and lifecycle state.
    """

    __tablename__ = "entity_relationships"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source_entity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("threat_entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_entity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("threat_entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relationship_type: Mapped[RelationshipType] = mapped_column(
        Enum(RelationshipType, name="relationship_type_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    relationship_status: Mapped[RelationshipStatus] = mapped_column(
        Enum(RelationshipStatus, name="relationship_status_enum", native_enum=False),
        default=RelationshipStatus.CANDIDATE,
        nullable=False,
        index=True,
    )
    evidence_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evidences.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    evidence_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    source_entity: Mapped["ThreatEntity"] = relationship(
        "ThreatEntity",
        foreign_keys=[source_entity_id],
        back_populates="outgoing_relationships",
        lazy="selectin",
    )
    target_entity: Mapped["ThreatEntity"] = relationship(
        "ThreatEntity",
        foreign_keys=[target_entity_id],
        back_populates="incoming_relationships",
        lazy="selectin",
    )
    evidence: Mapped[Optional["Evidence"]] = relationship(
        "Evidence",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint(
            "source_entity_id",
            "target_entity_id",
            "relationship_type",
            name="uq_entity_relationship_source_target_type",
        ),
        Index("ix_entity_relationships_source_status", "source_entity_id", "relationship_status"),
    )
