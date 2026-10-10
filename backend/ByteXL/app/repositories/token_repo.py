from datetime import datetime, timezone
from typing import Optional
import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.token import RefreshToken


class TokenRepository:
    """Data access repository for refresh token lifecycle management."""

    async def create(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:
        """Store a new hashed refresh token."""
        record = RefreshToken(
            id=uuid.uuid4(),
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_revoked=False,
        )
        db.add(record)
        await db.flush()
        await db.refresh(record)
        return record

    async def get_by_hash(
        self,
        db: AsyncSession,
        token_hash: str,
    ) -> Optional[RefreshToken]:
        """Fetch token by exact SHA-256 hash."""
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke(
        self,
        db: AsyncSession,
        record: RefreshToken,
    ) -> None:
        """Mark specific refresh token record as revoked."""
        record.is_revoked = True
        record.revoked_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(record)

    async def revoke_all_for_user(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> None:
        """Revoke all active refresh tokens belonging to a user (e.g. global logout)."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.is_revoked.is_(False))
            .values(is_revoked=True, revoked_at=now)
        )
        await db.execute(stmt)
        await db.flush()
