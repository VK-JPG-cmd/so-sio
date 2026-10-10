from typing import List, Optional
import uuid
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.enums import ReviewStatus
from app.models.review import Review


class ReviewRepository:
    """Data access repository for customer reviews."""

    async def create(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        customer_id: uuid.UUID,
        rating: int,
        body: str,
        status: ReviewStatus = ReviewStatus.PENDING_MODERATION,
    ) -> Review:
        """Create and persist a new customer review."""
        review = Review(
            id=uuid.uuid4(),
            brand_id=brand_id,
            customer_id=customer_id,
            rating=rating,
            body=body,
            status=status,
        )
        db.add(review)
        await db.flush()
        await db.refresh(review)
        return review

    async def get_by_id(
        self,
        db: AsyncSession,
        review_id: uuid.UUID,
    ) -> Optional[Review]:
        """Fetch review by UUID."""
        stmt = select(Review).where(Review.id == review_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_brand(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        status: Optional[ReviewStatus] = ReviewStatus.PUBLISHED,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Review]:
        """Fetch reviews for a specific brand, optionally filtered by status with pagination."""
        stmt = select(Review).where(Review.brand_id == brand_id)
        if status is not None:
            stmt = stmt.where(Review.status == status)
        stmt = stmt.order_by(desc(Review.created_at)).offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_customer(
        self,
        db: AsyncSession,
        customer_id: uuid.UUID,
        status: Optional[ReviewStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Review]:
        """Fetch all reviews authored by a specific customer."""
        stmt = select(Review).where(Review.customer_id == customer_id)
        if status is not None:
            stmt = stmt.where(Review.status == status)
        stmt = stmt.order_by(desc(Review.created_at)).offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def count_by_customer(
        self,
        db: AsyncSession,
        customer_id: uuid.UUID,
        status: Optional[ReviewStatus] = None,
    ) -> int:
        """Count total reviews authored by a specific customer."""
        stmt = select(func.count(Review.id)).where(Review.customer_id == customer_id)
        if status is not None:
            stmt = stmt.where(Review.status == status)
        result = await db.execute(stmt)
        return result.scalar() or 0

    async def update(
        self,
        db: AsyncSession,
        review: Review,
    ) -> Review:
        """Persist changes to an existing review record."""
        await db.flush()
        await db.refresh(review)
        return review
