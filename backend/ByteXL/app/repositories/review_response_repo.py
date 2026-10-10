from typing import Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.review_response import ReviewResponse


class ReviewResponseRepository:
    """Data access repository for official brand owner responses to reviews."""

    async def get_by_review_id(
        self,
        db: AsyncSession,
        review_id: uuid.UUID,
    ) -> Optional[ReviewResponse]:
        """Fetch existing owner response for a specific review."""
        stmt = select(ReviewResponse).where(ReviewResponse.review_id == review_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_or_update(
        self,
        db: AsyncSession,
        review_id: uuid.UUID,
        brand_id: uuid.UUID,
        responder_user_id: uuid.UUID,
        response_text: str,
    ) -> ReviewResponse:
        """Create a new owner response or update an existing one."""
        existing = await self.get_by_review_id(db, review_id)
        if existing:
            existing.response_text = response_text
            existing.responder_user_id = responder_user_id
            await db.flush()
            await db.refresh(existing)
            return existing

        new_response = ReviewResponse(
            id=uuid.uuid4(),
            review_id=review_id,
            brand_id=brand_id,
            responder_user_id=responder_user_id,
            response_text=response_text,
        )
        db.add(new_response)
        await db.flush()
        await db.refresh(new_response)
        return new_response
