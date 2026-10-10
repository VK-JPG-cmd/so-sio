from datetime import datetime, timezone
from typing import Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.domain_challenge import DomainChallenge


class DomainChallengeRepository:
    """Data access repository for DomainChallenge entities."""

    async def create(
        self,
        db: AsyncSession,
        application_id: uuid.UUID,
        challenge_hash: str,
        record_host: str,
        expires_at: datetime,
        max_attempts: int = 5,
    ) -> DomainChallenge:
        """Persist a new DNS domain challenge record."""
        challenge = DomainChallenge(
            id=uuid.uuid4(),
            application_id=application_id,
            challenge_hash=challenge_hash,
            record_host=record_host,
            expires_at=expires_at,
            max_attempts=max_attempts,
            attempts_count=0,
        )
        db.add(challenge)
        await db.flush()
        await db.refresh(challenge)
        return challenge

    async def get_latest_for_application(
        self,
        db: AsyncSession,
        application_id: uuid.UUID,
    ) -> Optional[DomainChallenge]:
        """Fetch the most recently generated domain challenge for an application."""
        stmt = (
            select(DomainChallenge)
            .where(DomainChallenge.application_id == application_id)
            .order_by(DomainChallenge.created_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def increment_attempt(
        self,
        db: AsyncSession,
        challenge: DomainChallenge,
    ) -> DomainChallenge:
        """Increment challenge verification attempt count."""
        challenge.attempts_count += 1
        await db.flush()
        await db.refresh(challenge)
        return challenge

    async def mark_verified(
        self,
        db: AsyncSession,
        challenge: DomainChallenge,
    ) -> DomainChallenge:
        """Mark challenge as successfully verified."""
        challenge.verified_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(challenge)
        return challenge
