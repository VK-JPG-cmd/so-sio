from datetime import datetime
from typing import TYPE_CHECKING
import uuid
from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.threat_entity import ThreatEntity


class CampaignMembership(Base):
    """
    Associates an individual threat entity with an overarching threat campaign.
    Documents the specific defensible reason for inclusion.
    """

    __tablename__ = "campaign_memberships"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("threat_entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relationship_reason: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    campaign: Mapped["Campaign"] = relationship(
        "Campaign",
        back_populates="memberships",
        lazy="selectin",
    )
    entity: Mapped["ThreatEntity"] = relationship(
        "ThreatEntity",
        back_populates="campaign_memberships",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("campaign_id", "entity_id", name="uq_campaign_membership_campaign_entity"),
        Index("ix_campaign_memberships_campaign_created", "campaign_id", "created_at"),
    )
