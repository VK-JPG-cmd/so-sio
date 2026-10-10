from datetime import datetime
from typing import TYPE_CHECKING, Optional
import uuid
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.brand_application import BrandApplication


class DomainChallenge(Base):
    """DNS TXT ownership challenge generated for a brand application."""

    __tablename__ = "domain_challenges"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("brand_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    challenge_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    record_host: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    attempts_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    max_attempts: Mapped[int] = mapped_column(
        Integer,
        default=5,
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    application: Mapped["BrandApplication"] = relationship(
        "BrandApplication",
        back_populates="challenges",
    )

    __table_args__ = (
        Index("ix_challenges_app_created", "application_id", "created_at"),
    )
