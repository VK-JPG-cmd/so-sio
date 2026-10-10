import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.review import ReviewResponse, ReviewUpdate
from app.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["Reviews"])
review_service = ReviewService()


@router.patch(
    "/{review_id}",
    response_model=ReviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Update review or moderate status",
    description=(
        "Enforces review ownership: Authors may update rating and body (resetting status to PENDING_MODERATION). "
        "Administrators may moderate review status (PUBLISHED, REJECTED). "
        "Unauthorized modification attempts by other users are rejected with 403 Forbidden."
    ),
)
async def update_review(
    review_id: uuid.UUID,
    payload: ReviewUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ReviewResponse:
    review = await review_service.update_review(
        db=db,
        review_id=review_id,
        current_user=current_user,
        payload=payload,
    )
    return ReviewResponse.model_validate(review)
