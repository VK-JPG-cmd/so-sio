from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
import uuid
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import CampaignStatus

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.brand import Brand
    from app.models.campaign_membership import CampaignMembership


class Campaign(Base):
    """
    Correlated cluster of threat entities exhibiting evidence-backed relationships.
    Groups attacks, lookalikes, or infrastructure targeting a specific brand.
    """

    __tablename__ = "campaigns"

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
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus, name="campaign_status_enum", native_enum=False),
        default=CampaignStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    risk_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
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
    memberships: Mapped[List["CampaignMembership"]] = relationship(
        "CampaignMembership",
        back_populates="campaign",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    alerts: Mapped[List["Alert"]] = relationship(
        "Alert",
        back_populates="campaign",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_campaigns_brand_status", "brand_id", "status"),
        Index("ix_campaigns_brand_created", "brand_id", "created_at"),
    )
