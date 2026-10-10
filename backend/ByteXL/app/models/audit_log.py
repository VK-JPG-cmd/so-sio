from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional
import uuid
from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.brand import Brand
    from app.models.user import User


class AuditLog(Base):
    """
    Immutable audit log entry recording sensitive brand operations and status modifications.
    Captures actor ID, brand context, action category, entity identifiers, and payload state diffs.
    """

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    actor_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    brand_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    entity_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
    )
    details: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    actor: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
    )
    brand: Mapped[Optional["Brand"]] = relationship(
        "Brand",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_audit_logs_brand_created", "brand_id", "created_at"),
        Index("ix_audit_logs_action_created", "action", "created_at"),
    )


from sqlalchemy import event


@event.listens_for(AuditLog, "before_update")
def prevent_audit_log_update(mapper: Any, connection: Any, target: Any) -> None:
    raise PermissionError("Audit log entries are strictly immutable and cannot be modified.")


@event.listens_for(AuditLog, "before_delete")
def prevent_audit_log_delete(mapper: Any, connection: Any, target: Any) -> None:
    raise PermissionError("Audit log entries are strictly immutable and cannot be deleted.")

