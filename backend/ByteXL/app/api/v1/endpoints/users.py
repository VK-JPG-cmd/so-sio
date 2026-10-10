from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.dependencies import (
    get_current_active_user,
    get_current_user,
    require_admin,
    require_brand_owner,
)
from app.db.session import get_db
from app.models.enums import ReviewStatus, ThreatReportStatus
from app.models.user import User
from app.schemas.review import ReviewResponse
from app.schemas.threat_report import ThreatReportResponse
from app.schemas.user import UserProfileResponse
from app.services.review_service import ReviewService
from app.services.threat_report_service import ThreatReportService

router = APIRouter(prefix="/users", tags=["Users"])
review_service = ReviewService()
threat_report_service = ThreatReportService()


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Returns the profile information of the currently authenticated user.",
)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
) -> UserProfileResponse:
    """Return only sanitized profile fields for the authenticated caller."""
    return UserProfileResponse.model_validate(current_user)


@router.get(
    "/me/reviews",
    response_model=List[ReviewResponse],
    status_code=status.HTTP_200_OK,
    summary="Get my submitted brand reviews",
    description="Returns all reviews authored by the currently authenticated user across moderation states with pagination and filtering.",
)
async def get_my_reviews(
    response: Response,
    status_filter: Optional[ReviewStatus] = Query(default=None, alias="status", description="Filter by review status"),
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    limit: Optional[int] = Query(default=None, ge=1, le=100, description="Raw limit override"),
    offset: Optional[int] = Query(default=None, ge=0, description="Raw offset override"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[ReviewResponse]:
    eff_limit = limit if limit is not None else page_size
    eff_offset = offset if offset is not None else (page - 1) * page_size
    eff_page = (eff_offset // eff_limit) + 1 if eff_limit > 0 else 1

    total = await review_service.count_my_reviews(
        db=db,
        current_user=current_user,
        status=status_filter,
    )
    reviews = await review_service.get_my_reviews(
        db=db,
        current_user=current_user,
        status=status_filter,
        limit=eff_limit,
        offset=eff_offset,
    )
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page"] = str(eff_page)
    response.headers["X-Page-Size"] = str(eff_limit)
    return [ReviewResponse.model_validate(r) for r in reviews]


@router.get(
    "/me/threat-reports",
    response_model=List[ThreatReportResponse],
    status_code=status.HTTP_200_OK,
    summary="Get my submitted threat reports",
    description="Returns all threat reports submitted by the currently authenticated customer with status, evidence, pagination, and filtering.",
)
async def get_my_threat_reports(
    response: Response,
    status_filter: Optional[ThreatReportStatus] = Query(default=None, alias="status", description="Filter by report status"),
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    limit: Optional[int] = Query(default=None, ge=1, le=100, description="Raw limit override"),
    offset: Optional[int] = Query(default=None, ge=0, description="Raw offset override"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[ThreatReportResponse]:
    eff_limit = limit if limit is not None else page_size
    eff_offset = offset if offset is not None else (page - 1) * page_size
    eff_page = (eff_offset // eff_limit) + 1 if eff_limit > 0 else 1

    total = await threat_report_service.count_my_reports(
        db=db,
        current_user=current_user,
        status=status_filter,
    )
    reports = await threat_report_service.get_my_reports(
        db=db,
        current_user=current_user,
        status=status_filter,
        limit=eff_limit,
        offset=eff_offset,
    )
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page"] = str(eff_page)
    response.headers["X-Page-Size"] = str(eff_limit)
    return [ThreatReportResponse.model_validate(r) for r in reports]


@router.get(
    "/admin-panel",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Admin-only diagnostic endpoint",
    description="Enforces ADMIN role requirement to verify role-based access control.",
)
async def get_admin_data(
    current_admin: User = Depends(require_admin),
) -> UserProfileResponse:
    return UserProfileResponse.model_validate(current_admin)


@router.get(
    "/brand-portal",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Brand owner diagnostic endpoint",
    description="Enforces BRAND_OWNER role requirement to verify role-based access control.",
)
async def get_brand_owner_data(
    current_brand_owner: User = Depends(require_brand_owner),
) -> UserProfileResponse:
    return UserProfileResponse.model_validate(current_brand_owner)
