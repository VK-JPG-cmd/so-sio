from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.dependencies import get_current_active_user, require_customer
from app.db.session import get_db
from app.models.enums import BrandVerificationStatus
from app.models.user import User
from app.schemas.brand import (
    BrandAssetCreate,
    BrandAssetResponse,
    PublicBrandDetailResponse,
    PublicBrandResponse,
)
from app.schemas.review import (
    ReviewCreate,
    ReviewPublicResponse,
    ReviewResponse,
)
from app.services.brand_service import BrandService
from app.services.review_service import ReviewService

router = APIRouter(prefix="/brands", tags=["Brands"])
brand_service = BrandService()
review_service = ReviewService()


@router.get(
    "",
    response_model=List[PublicBrandResponse],
    status_code=status.HTTP_200_OK,
    summary="Public brand discovery",
    description="List public verified brand profiles with search, pagination, and status filtering. Never leaks private ownership data.",
)
async def list_brands(
    response: Response,
    search: Optional[str] = Query(default=None, description="Search by brand display name or official domain"),
    verification_status: Optional[BrandVerificationStatus] = Query(
        default=None, description="Filter by brand verification status"
    ),
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    limit: Optional[int] = Query(default=None, ge=1, le=100),
    offset: Optional[int] = Query(default=None, ge=0),
    db: AsyncSession = Depends(get_db),
) -> List[PublicBrandResponse]:
    actual_limit = limit if limit is not None else page_size
    actual_offset = offset if offset is not None else (page - 1) * page_size

    brands = await brand_service.list_public_brands(
        db, search=search, status=verification_status, limit=actual_limit, offset=actual_offset
    )
    total = await brand_service.count_public_brands(db, search=search, status=verification_status)

    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page"] = str(page)
    response.headers["X-Page-Size"] = str(actual_limit)
    return [PublicBrandResponse.model_validate(b) for b in brands]


@router.get(
    "/{id}",
    response_model=PublicBrandDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get public brand profile",
    description="Retrieve approved public profile details for a brand including safe public metadata and approved published reviews.",
)
async def get_brand_profile(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> PublicBrandDetailResponse:
    brand, published_reviews = await brand_service.get_public_brand_detail(db, id)
    return PublicBrandDetailResponse(
        id=brand.id,
        display_name=brand.display_name,
        official_domain=brand.official_domain,
        verification_status=brand.verification_status,
        created_at=brand.created_at,
        published_reviews=[ReviewPublicResponse.model_validate(r) for r in published_reviews],
    )


@router.post(
    "/{id}/assets",
    response_model=BrandAssetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register brand asset",
    description="Upload official brand asset metadata into secure private storage with content hashing.",
)
async def create_brand_asset(
    id: uuid.UUID,
    payload: BrandAssetCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> BrandAssetResponse:
    asset = await brand_service.add_brand_asset(db, id, payload, current_user)
    return BrandAssetResponse.model_validate(asset)


@router.get(
    "/{id}/assets",
    response_model=List[BrandAssetResponse],
    status_code=status.HTTP_200_OK,
    summary="List brand assets",
    description="Retrieve official asset metadata for a brand. Restricted to brand owner or administrator.",
)
async def list_brand_assets(
    id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[BrandAssetResponse]:
    assets = await brand_service.list_brand_assets(db, id, current_user)
    return [BrandAssetResponse.model_validate(a) for a in assets]


@router.post(
    "/{brand_id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit brand review",
    description="Allows authenticated customers to submit a review for a verified brand. Initial status is PENDING_MODERATION.",
)
async def create_brand_review(
    brand_id: uuid.UUID,
    payload: ReviewCreate,
    current_customer: User = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
) -> ReviewResponse:
    review = await review_service.create_review(
        db=db,
        brand_id=brand_id,
        current_user=current_customer,
        payload=payload,
    )
    return ReviewResponse.model_validate(review)


@router.get(
    "/{brand_id}/reviews",
    response_model=List[ReviewPublicResponse],
    status_code=status.HTTP_200_OK,
    summary="List published brand reviews",
    description="Retrieve publicly visible published reviews for a brand. Unmoderated or rejected reviews are omitted.",
)
async def list_brand_reviews(
    brand_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> List[ReviewPublicResponse]:
    reviews = await review_service.get_published_brand_reviews(
        db=db,
        brand_id=brand_id,
        limit=limit,
        offset=offset,
    )
    return [ReviewPublicResponse.model_validate(r) for r in reviews]

