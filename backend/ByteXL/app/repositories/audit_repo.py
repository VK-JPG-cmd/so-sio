from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog


class AuditLogRepository:
    """Data access repository for immutable system audit logs."""

    async def create_log(
        self,
        db: AsyncSession,
        actor_user_id: uuid.UUID,
        action: str,
        entity_type: str,
        entity_id: str,
        details: Dict[str, Any],
        brand_id: Optional[uuid.UUID] = None,
    ) -> AuditLog:
        """Create and persist a new audit log record."""
        log = AuditLog(
            id=uuid.uuid4(),
            actor_user_id=actor_user_id,
            brand_id=brand_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )
        db.add(log)
        await db.flush()
        await db.refresh(log)
        return log

    async def list_logs_for_brand(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
        action: Optional[str] = None,
    ) -> List[AuditLog]:
        """Fetch historical audit log records for a given brand with pagination."""
        stmt = (
            select(AuditLog)
            .where(AuditLog.brand_id == brand_id)
            .order_by(desc(AuditLog.created_at))
            .offset(offset)
            .limit(limit)
        )
        if action:
            stmt = stmt.where(AuditLog.action == action)

        result = await db.execute(stmt)
        return list(result.scalars().all())
