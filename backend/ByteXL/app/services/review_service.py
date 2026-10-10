from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import (
    AuthorizationError,
    NotFoundError,
    ValidationError,
)
from app.core.logging import get_logger
from app.models.enums import BrandVerificationStatus, ReviewStatus, UserRole
from app.models.review import Review
from app.models.user import User
from app.repositories.brand_repo import BrandRepository
from app.repositories.review_repo import ReviewRepository
from app.schemas.review import ReviewCreate, ReviewUpdate

logger = get_logger("app.services.review_service")


from app.repositories.audit_repo import AuditLogRepository


class ReviewService:
    """
    Business logic for customer brand reviews, review ownership,
    and moderation lifecycle workflows.
    """

    def __init__(self) -> None:
        self.review_repo = ReviewRepository()
        self.brand_repo = BrandRepository()
        self.audit_repo = AuditLogRepository()

    async def create_review(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        current_user: User,
        payload: ReviewCreate,
    ) -> Review:
        """
        Submit a new customer brand review.
        Enforces customer role, verifies target brand existence,
        and initializes moderation status to PENDING_MODERATION.

        Policy Note:
        - Negative reviews (1 or 2 stars) are NEVER automatically classified as fake or malicious.
        - Phone verification validates identity/possession, NOT proof of genuine purchase.
        """
        if current_user.role != UserRole.CUSTOMER and current_user.role != UserRole.ADMIN:
            raise AuthorizationError("Only customers may submit brand reviews.")

        brand = await self.brand_repo.get_by_id(db, brand_id)
        if not brand:
            raise NotFoundError(f"Brand with id '{brand_id}' not found.")

        if brand.verification_status != BrandVerificationStatus.VERIFIED:
            raise ValidationError(
                f"Cannot review brand with status '{brand.verification_status.value}'. "
                "Only verified brands accept reviews."
            )

        review = await self.review_repo.create(
            db=db,
            brand_id=brand_id,
            customer_id=current_user.id,
            rating=payload.rating,
            body=payload.body,
            status=ReviewStatus.PENDING_MODERATION,
        )
        await db.commit()
        logger.info(
            f"Review {review.id} submitted for brand {brand_id} by user {current_user.id} "
            f"(rating={review.rating}, status={review.status.value})"
        )
        return review

    async def get_published_brand_reviews(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Review]:
        """
        Retrieve published reviews for a brand.
        Never exposes unmoderated, pending, or rejected reviews to the public.
        """
        brand = await self.brand_repo.get_by_id(db, brand_id)
        if not brand:
            raise NotFoundError(f"Brand with id '{brand_id}' not found.")

        return await self.review_repo.get_by_brand(
            db=db,
            brand_id=brand_id,
            status=ReviewStatus.PUBLISHED,
            limit=limit,
            offset=offset,
        )

    async def get_my_reviews(
        self,
        db: AsyncSession,
        current_user: User,
        status: Optional[ReviewStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Review]:
        """
        Retrieve all reviews submitted by the currently authenticated user,
        optionally filtered by moderation status.
        """
        return await self.review_repo.get_by_customer(
            db=db,
            customer_id=current_user.id,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def count_my_reviews(
        self,
        db: AsyncSession,
        current_user: User,
        status: Optional[ReviewStatus] = None,
    ) -> int:
        """Count total reviews submitted by the currently authenticated user."""
        return await self.review_repo.count_by_customer(
            db=db,
            customer_id=current_user.id,
            status=status,
        )

    async def update_review(
        self,
        db: AsyncSession,
        review_id: uuid.UUID,
        current_user: User,
        payload: ReviewUpdate,
    ) -> Review:
        """
        Modify an existing review or moderate its lifecycle status:
        - Review author (Customer) may update rating and body. Doing so re-submits
          the review for moderation (status -> PENDING_MODERATION).
        - Platform Administrator may moderate status (PUBLISHED, REJECTED, PENDING_MODERATION).
        - Cross-customer modification attempts are strictly forbidden (403 Forbidden).
        """
        review = await self.review_repo.get_by_id(db, review_id)
        if not review:
            raise NotFoundError(f"Review with id '{review_id}' not found.")

        is_author = review.customer_id == current_user.id
        is_admin = current_user.role == UserRole.ADMIN

        if not is_author and not is_admin:
            logger.warning(
                f"Unauthorized review edit attempt: user {current_user.id} tried to edit "
                f"review {review_id} owned by {review.customer_id}"
            )
            raise AuthorizationError("You do not have permission to modify this review.")

        # Admin moderation branch
        if is_admin and payload.status is not None:
            old_status = review.status
            review.status = payload.status
            await self.audit_repo.create_log(
                db=db,
                actor_user_id=current_user.id,
                action="REVIEW_MODERATION",
                entity_type="REVIEW",
                entity_id=str(review.id),
                details={"old_status": old_status.value, "new_status": review.status.value},
                brand_id=review.brand_id,
            )
            logger.info(f"Admin {current_user.id} updated review {review_id} status to {review.status.value}")

        # Author edit branch (or admin editing text)
        if is_author:
            if payload.rating is not None:
                review.rating = payload.rating
            if payload.body is not None:
                review.body = payload.body

            # Edits by customer require re-moderation unless already an admin action
            if not is_admin:
                review.status = ReviewStatus.PENDING_MODERATION

        elif is_admin and not is_author:
            if payload.rating is not None:
                review.rating = payload.rating
            if payload.body is not None:
                review.body = payload.body

        await self.review_repo.update(db, review)
        await db.commit()
        return review
