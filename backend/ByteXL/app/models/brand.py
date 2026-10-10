from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
import uuid
from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import BrandVerificationStatus

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.audit_log import AuditLog
    from app.models.brand_application import BrandApplication
    from app.models.brand_asset import BrandAsset
    from app.models.official_mobile_asset import BrandMobileApp
    from app.models.official_social_asset import BrandSocialAsset
    from app.models.campaign import Campaign
    from app.models.review import Review
    from app.models.review_response import ReviewResponse
    from app.models.user import User


class Brand(Base):
    """Verified brand entity representing an authenticated digital brand presence."""

    __tablename__ = "brands"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("brand_applications.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    display_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    official_domain: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    verification_status: Mapped[BrandVerificationStatus] = mapped_column(
        Enum(BrandVerificationStatus, name="brand_verification_status_enum", native_enum=False),
        default=BrandVerificationStatus.VERIFIED,
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
    application: Mapped["BrandApplication"] = relationship(
        "BrandApplication",
        back_populates="brand",
    )
    owner: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
    )
    assets: Mapped[List["BrandAsset"]] = relationship(
        "BrandAsset",
        back_populates="brand",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    social_assets: Mapped[List["BrandSocialAsset"]] = relationship(
        "BrandSocialAsset",
        back_populates="brand",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    mobile_apps: Mapped[List["BrandMobileApp"]] = relationship(
        "BrandMobileApp",
        back_populates="brand",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="brand",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    campaigns: Mapped[List["Campaign"]] = relationship(
        "Campaign",
        back_populates="brand",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    alerts: Mapped[List["Alert"]] = relationship(
        "Alert",
        back_populates="brand",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="brand",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    review_responses: Mapped[List["ReviewResponse"]] = relationship(
        "ReviewResponse",
        back_populates="brand",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_brands_status_domain", "verification_status", "official_domain"),
    )
