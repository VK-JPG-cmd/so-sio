from datetime import datetime
from typing import TYPE_CHECKING
import uuid
from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import EvidenceType

if TYPE_CHECKING:
    from app.models.threat_report import ThreatReport


class Evidence(Base):
    """Secure artifact evidence metadata attached to customer threat reports."""

    __tablename__ = "evidences"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("threat_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evidence_type: Mapped[EvidenceType] = mapped_column(
        Enum(EvidenceType, name="evidence_type_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    storage_key: Mapped[str] = mapped_column(
        String(512),
        unique=True,
        nullable=False,
        index=True,
    )
    sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    report: Mapped["ThreatReport"] = relationship(
        "ThreatReport",
        back_populates="evidences",
    )

    __table_args__ = (
        Index("ix_evidences_report_created", "report_id", "created_at"),
    )
