from datetime import datetime, timezone
from typing import Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.enums import AccountStatus, UserRole
from app.models.user import User


class UserRepository:
    """Data access repository for User entities."""

    async def get_by_id(self, db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        """Fetch user by primary key UUID."""
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_phone(self, db: AsyncSession, phone_number: str) -> Optional[User]:
        """Fetch user by unique phone number."""
        stmt = select(User).where(User.phone_number == phone_number)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        db: AsyncSession,
        phone_number: str,
        role: UserRole = UserRole.CUSTOMER,
        account_status: AccountStatus = AccountStatus.ACTIVE,
    ) -> User:
        """Create and persist a new user entity."""
        now = datetime.now(timezone.utc)
        user = User(
            id=uuid.uuid4(),
            phone_number=phone_number,
            phone_verified_at=now,
            role=role,
            account_status=account_status,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    async def mark_verified(self, db: AsyncSession, user: User) -> User:
        """Update user status to verified and active."""
        user.phone_verified_at = datetime.now(timezone.utc)
        if user.account_status == AccountStatus.PENDING_VERIFICATION:
            user.account_status = AccountStatus.ACTIVE
        await db.flush()
        await db.refresh(user)
        return user
