from datetime import datetime
from typing import TYPE_CHECKING, List
import uuid
from sqlalchemy import DateTime, Enum, Index, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import EntityType

if TYPE_CHECKING:
    from app.models.campaign_membership import CampaignMembership
    from app.models.entity_relationship import EntityRelationship


class ThreatEntity(Base):
    """
    Canonical, deduplicated threat indicator entity (domain, URL, IP, profile, hash, package).
    """

    __tablename__ = "threat_entities"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    entity_type: Mapped[EntityType] = mapped_column(
        Enum(EntityType, name="entity_type_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    canonical_value: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
        index=True,
    )
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    outgoing_relationships: Mapped[List["EntityRelationship"]] = relationship(
        "EntityRelationship",
        foreign_keys="EntityRelationship.source_entity_id",
        back_populates="source_entity",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    incoming_relationships: Mapped[List["EntityRelationship"]] = relationship(
        "EntityRelationship",
        foreign_keys="EntityRelationship.target_entity_id",
        back_populates="target_entity",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    campaign_memberships: Mapped[List["CampaignMembership"]] = relationship(
        "CampaignMembership",
        back_populates="entity",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("entity_type", "canonical_value", name="uq_threat_entity_type_canonical"),
        Index("ix_threat_entities_type_last_seen", "entity_type", "last_seen_at"),
    )
