from typing import List
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.brand_application import (
    BrandApplicationCreate,
    BrandApplicationResponse,
    DomainChallengeResponse,
    DomainVerifyRequest,
    DomainVerifyResponse,
)
from app.services.brand_service import BrandService

router = APIRouter(prefix="/brand-applications", tags=["Brand Applications"])
brand_service = BrandService()


@router.post(
    "",
    response_model=BrandApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit brand application",
    description="Allows an authenticated applicant or brand owner to submit an official brand application.",
)
async def create_brand_application(
    payload: BrandApplicationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> BrandApplicationResponse:
    app_entity = await brand_service.create_application(db, current_user, payload)
    return BrandApplicationResponse.model_validate(app_entity)


@router.get(
    "/me",
    response_model=List[BrandApplicationResponse],
    status_code=status.HTTP_200_OK,
    summary="View my brand applications",
    description="Returns all applications submitted by the currently authenticated user.",
)
async def get_my_applications(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[BrandApplicationResponse]:
    apps = await brand_service.get_my_applications(db, current_user.id)
    return [BrandApplicationResponse.model_validate(a) for a in apps]


@router.post(
    "/{id}/domain-challenge",
    response_model=DomainChallengeResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate domain verification DNS challenge",
    description=(
        "Generates a cryptographically random challenge token and provides the exact "
        "DNS TXT record host and value to configure for ownership verification."
    ),
)
async def generate_domain_challenge(
    id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DomainChallengeResponse:
    return await brand_service.generate_domain_challenge(db, id, current_user)


@router.post(
    "/{id}/verify-domain",
    response_model=DomainVerifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify DNS TXT record for domain",
    description=(
        "Performs authoritative live DNS TXT record lookup to verify domain ownership. "
        "Enforces attempt limits, challenge expiration, and ownership checks."
    ),
)
async def verify_domain(
    id: uuid.UUID,
    payload: DomainVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DomainVerifyResponse:
    return await brand_service.verify_domain(db, id, payload.token, current_user)
