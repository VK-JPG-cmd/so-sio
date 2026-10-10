from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
import uuid
from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import ApplicationStatus

if TYPE_CHECKING:
    from app.models.brand import Brand
    from app.models.domain_challenge import DomainChallenge
    from app.models.user import User


class BrandApplication(Base):
    """Application submitted by an organization to register an official brand."""

    __tablename__ = "brand_applications"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    business_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    official_domain: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    application_status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="application_status_enum", native_enum=False),
        default=ApplicationStatus.PENDING_DOMAIN_VERIFICATION,
        nullable=False,
        index=True,
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
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
    owner: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
    )
    challenges: Mapped[List["DomainChallenge"]] = relationship(
        "DomainChallenge",
        back_populates="application",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    brand: Mapped[Optional["Brand"]] = relationship(
        "Brand",
        back_populates="application",
        uselist=False,
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_brand_apps_owner_status", "owner_user_id", "application_status"),
        Index("ix_brand_apps_domain", "official_domain"),
    )
