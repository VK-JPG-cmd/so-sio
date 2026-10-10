from datetime import datetime, timezone
from typing import Optional
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.otp import OTPVerification


class OTPRepository:
    """Data access repository for OTP verifications and rate limiting."""

    async def get_recent_count(
        self,
        db: AsyncSession,
        phone_number: str,
        since: datetime,
    ) -> int:
        """Count number of OTPs requested by phone number since given timestamp."""
        stmt = (
            select(func.count(OTPVerification.id))
            .where(OTPVerification.phone_number == phone_number)
            .where(OTPVerification.created_at >= since)
        )
        result = await db.execute(stmt)
        return int(result.scalar_one() or 0)

    async def get_latest_active(
        self,
        db: AsyncSession,
        phone_number: str,
    ) -> Optional[OTPVerification]:
        """Fetch the most recently created OTP record for a phone number."""
        stmt = (
            select(OTPVerification)
            .where(OTPVerification.phone_number == phone_number)
            .order_by(OTPVerification.created_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        db: AsyncSession,
        phone_number: str,
        hashed_code: str,
        salt: str,
        expires_at: datetime,
        max_attempts: int,
    ) -> OTPVerification:
        """Persist a new hashed OTP verification record."""
        record = OTPVerification(
            id=uuid.uuid4(),
            phone_number=phone_number,
            hashed_code=hashed_code,
            salt=salt,
            expires_at=expires_at,
            attempts_count=0,
            max_attempts=max_attempts,
            is_used=False,
        )
        db.add(record)
        await db.flush()
        await db.refresh(record)
        return record

    async def increment_attempt(
        self,
        db: AsyncSession,
        record: OTPVerification,
    ) -> OTPVerification:
        """Increment failed attempts counter."""
        record.attempts_count += 1
        await db.flush()
        await db.refresh(record)
        return record

    async def mark_used(
        self,
        db: AsyncSession,
        record: OTPVerification,
    ) -> OTPVerification:
        """Mark OTP verification record as successfully consumed."""
        record.is_used = True
        await db.flush()
        await db.refresh(record)
        return record
