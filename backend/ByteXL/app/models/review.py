from datetime import datetime
from typing import TYPE_CHECKING, Optional
import uuid
from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import ReviewStatus

if TYPE_CHECKING:
    from app.models.brand import Brand
    from app.models.review_response import ReviewResponse
    from app.models.user import User


class Review(Base):
    """Customer review entity for brand reputation and integrity tracking."""

    __tablename__ = "reviews"

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
    customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus, name="review_status_enum", native_enum=False),
        default=ReviewStatus.PENDING_MODERATION,
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
        back_populates="reviews",
        lazy="selectin",
    )
    customer: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
    )
    owner_response: Mapped[Optional["ReviewResponse"]] = relationship(
        "ReviewResponse",
        back_populates="review",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_review_rating_range"),
        Index("ix_reviews_brand_status", "brand_id", "status"),
        Index("ix_reviews_customer_created", "customer_id", "created_at"),
    )
