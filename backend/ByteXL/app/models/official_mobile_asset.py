from datetime import datetime
from typing import TYPE_CHECKING, Optional
import uuid
from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import AssetVerificationStatus

if TYPE_CHECKING:
    from app.models.brand import Brand


class BrandMobileApp(Base):
    """Metadata tracking official registered brand mobile applications."""

    __tablename__ = "brand_mobile_apps"

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
    app_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    platform: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    app_identifier: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    publisher_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    store_url: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )
    verification_status: Mapped[AssetVerificationStatus] = mapped_column(
        Enum(AssetVerificationStatus, name="asset_verification_status_enum", native_enum=False),
        default=AssetVerificationStatus.PENDING,
        nullable=False,
        index=True,
    )
    evidence: Mapped[Optional[str]] = mapped_column(
        String(1024),
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

    brand: Mapped["Brand"] = relationship(
        "Brand",
        back_populates="mobile_apps",
    )

    __table_args__ = (
        UniqueConstraint("brand_id", "platform", "app_identifier", name="uq_brand_mobile_app_identifier"),
        Index("ix_brand_mobile_apps_platform_identifier", "platform", "app_identifier"),
    )
