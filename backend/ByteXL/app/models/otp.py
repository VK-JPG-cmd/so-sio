from datetime import datetime
import uuid
from sqlalchemy import Boolean, DateTime, Index, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class OTPVerification(Base):
    """Stores cryptographically salted hashes of OTPs and verification attempts."""

    __tablename__ = "otp_verifications"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    phone_number: Mapped[str] = mapped_column(
        String(32),
        index=True,
        nullable=False,
    )
    hashed_code: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    salt: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    attempts_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    max_attempts: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
    )
    is_used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_otp_phone_created", "phone_number", "created_at"),
    )
