from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy import DateTime, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class DiscoveryCheckpoint(Base):
    """
    Persistent state checkpoint and operational telemetry tracker for a threat source connector.
    Guarantees incremental polling and supports health visibility.
    """

    __tablename__ = "discovery_checkpoints"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )
    checkpoint_value: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    last_poll_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_success_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_error_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    indicators_fetched_total: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    indicators_accepted_total: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    indicators_rejected_total: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    poll_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="IDLE",  # IDLE, POLLING, ERROR, NOT_CONFIGURED, DISABLED
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
