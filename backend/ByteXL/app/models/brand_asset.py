from datetime import datetime
from typing import TYPE_CHECKING
import uuid
from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import AssetType

if TYPE_CHECKING:
    from app.models.brand import Brand


class BrandAsset(Base):
    """Metadata tracking official brand digital assets stored in secure private storage."""

    __tablename__ = "brand_assets"

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
    asset_type: Mapped[AssetType] = mapped_column(
        Enum(AssetType, name="asset_type_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    storage_key: Mapped[str] = mapped_column(
        String(512),
        unique=True,
        nullable=False,
    )
    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    brand: Mapped["Brand"] = relationship(
        "Brand",
        back_populates="assets",
    )

    __table_args__ = (
        Index("ix_brand_assets_brand_type", "brand_id", "asset_type"),
    )
