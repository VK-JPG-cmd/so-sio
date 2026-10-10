from datetime import datetime
from typing import TYPE_CHECKING
import uuid
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.brand import Brand
    from app.models.review import Review
    from app.models.user import User


class ReviewResponse(Base):
    """
    Official brand owner response to a customer review.
    Enforces separation between customer reviews and owner replies,
    preventing owners from rewriting or deleting original customer reviews.
    """

    __tablename__ = "review_responses"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    review_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("reviews.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    brand_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    responder_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    response_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
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
    review: Mapped["Review"] = relationship(
        "Review",
        back_populates="owner_response",
        lazy="selectin",
    )
    brand: Mapped["Brand"] = relationship(
        "Brand",
        lazy="selectin",
    )
    responder: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_review_responses_brand_created", "brand_id", "created_at"),
    )
