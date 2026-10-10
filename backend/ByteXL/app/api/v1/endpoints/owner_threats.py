from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_active_user
from app.core.exceptions import BadRequestError, ForbiddenError
from app.db.session import get_db
from app.models.enums import AlertStatus, AssetVerificationStatus, CampaignStatus, ReviewStatus, RiskSeverity, ThreatReportStatus
from app.models.user import User
from app.schemas.brand import BrandAssetCreate, BrandAssetResponse, PublicBrandResponse
from app.schemas.correlation import (
    AlertResponse,
    BrandGraphResponse,
    CampaignResponse,
    CorrelationRunResponse,
)
from app.schemas.official_assets import (
    MobileAppCreate,
    MobileAppResponse,
    MobileAppUpdate,
    SocialAssetCreate,
    SocialAssetResponse,
    SocialAssetUpdate,
)
from app.schemas.owner_portal import (
    AlertStatusUpdate,
    AuditLogResponse,
    BrandDashboardSummaryResponse,
    BrandMetadataUpdate,
    ReviewOwnerResponseCreate,
    ReviewOwnerResponseDTO,
    ReviewWithOwnerResponseDTO,
)
from app.schemas.threat_report import ThreatReportResponse
from app.services.brand_service import BrandService
from app.services.correlation.campaign_service import CampaignCorrelationService
from app.services.official_asset_service import OfficialAssetService
from app.services.owner_portal_service import OwnerPortalService

router = APIRouter(prefix="/owner", tags=["Brand Owner Portal"])
owner_service = OwnerPortalService()
correlation_service = CampaignCorrelationService()
brand_service = BrandService()
official_asset_service = OfficialAssetService()


# -------------------------------------------------------------------------
# 1. Dashboard Summary
# -------------------------------------------------------------------------
@router.get(
    "/brands/{brand_id}/dashboard",
    response_model=BrandDashboardSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get brand owner dashboard summary",
    description="Retrieve aggregated live metrics including total reports, severity tiers, investigation status, recent alerts, campaign count, and historical risk score trends.",
)
async def get_brand_dashboard(
    brand_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> BrandDashboardSummaryResponse:
    await owner_service.verify_brand_ownership(db, brand_id, current_user)
    return await owner_service.get_dashboard_summary(db, brand_id)


# -------------------------------------------------------------------------
# 2. Threat Investigation
# -------------------------------------------------------------------------
@router.get(
    "/brands/{brand_id}/threats",
    response_model=List[ThreatReportResponse],
    status_code=status.HTTP_200_OK,
    summary="Get threats targeting authenticated brand",
    description="Retrieve threat incidents targeting the brand with pagination, sorting, severity tier, status, and date range filtering.",
)
async def get_brand_threats(
    brand_id: uuid.UUID,
    response: Response,
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    limit: Optional[int] = Query(default=None, ge=1, le=100, description="Limit override"),
    offset: Optional[int] = Query(default=None, ge=0, description="Offset override"),
    sort_by: str = Query(default="created_at", description="Sort field: created_at, status, target_value, target_type"),
    sort_order: str = Query(default="desc", description="Sort order: asc or desc"),
    severity: Optional[RiskSeverity] = Query(default=None, description="Filter by risk severity tier"),
    status_filter: Optional[ThreatReportStatus] = Query(default=None, alias="status", description="Filter by report status"),
    created_after: Optional[datetime] = Query(default=None, description="Filter reports created on or after"),
    created_before: Optional[datetime] = Query(default=None, description="Filter reports created on or before"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[ThreatReportResponse]:
    await owner_service.verify_brand_ownership(db, brand_id, current_user)

    actual_limit = limit if limit is not None else page_size
    actual_offset = offset if offset is not None else (page - 1) * page_size

    reports, total = await owner_service.list_brand_threats(
        db=db,
        brand_id=brand_id,
        limit=actual_limit,
        offset=actual_offset,
        sort_by=sort_by,
        sort_order=sort_order,
        severity=severity,
        status=status_filter,
        created_after=created_after,
        created_before=created_before,
    )

    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page"] = str(page)
    response.headers["X-Page-Size"] = str(actual_limit)
    return [ThreatReportResponse.model_validate(r) for r in reports]


# -------------------------------------------------------------------------
# 3. Campaign Management
# -------------------------------------------------------------------------
@router.get(
    "/brands/{brand_id}/campaigns",
    response_model=List[CampaignResponse],
    status_code=status.HTTP_200_OK,
    summary="Get correlated threat campaigns targeting brand",
    description="Retrieve clustered threat campaigns exhibiting evidence-backed relationships with pagination.",
)
async def get_brand_campaigns(
    brand_id: uuid.UUID,
    response: Response,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    limit: Optional[int] = Query(default=None, ge=1, le=100),
    offset: Optional[int] = Query(default=None, ge=0),
    status_filter: Optional[CampaignStatus] = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[CampaignResponse]:
    await owner_service.verify_brand_ownership(db, brand_id, current_user)

    actual_limit = limit if limit is not None else page_size
    actual_offset = offset if offset is not None else (page - 1) * page_size

    campaigns = await correlation_service.campaign_repo.list_by_brand(
        db=db,
        brand_id=brand_id,
        limit=actual_limit,
        offset=actual_offset,
    )
    if status_filter:
        campaigns = [c for c in campaigns if c.status == status_filter]

    response.headers["X-Total-Count"] = str(len(campaigns))
    return [CampaignResponse.model_validate(c) for c in campaigns]


# -------------------------------------------------------------------------
# 4. Alert Management
# -------------------------------------------------------------------------
@router.get(
    "/brands/{brand_id}/alerts",
    response_model=List[AlertResponse],
    status_code=status.HTTP_200_OK,
    summary="Get actionable brand threat alerts",
    description="Retrieve prioritized threat alerts for the brand with deduplication against unresolved incidents.",
)
async def get_brand_alerts(
    brand_id: uuid.UUID,
    response: Response,
    status_filter: Optional[AlertStatus] = Query(default=None, alias="status"),
    severity: Optional[RiskSeverity] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    limit: Optional[int] = Query(default=None, ge=1, le=100),
    offset: Optional[int] = Query(default=None, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[AlertResponse]:
    await owner_service.verify_brand_ownership(db, brand_id, current_user)

    actual_limit = limit if limit is not None else page_size
    actual_offset = offset if offset is not None else (page - 1) * page_size

    alerts = await correlation_service.alert_repo.list_by_brand(
        db=db,
        brand_id=brand_id,
        status=status_filter,
        severity=severity,
        limit=actual_limit,
        offset=actual_offset,
    )
    response.headers["X-Total-Count"] = str(len(alerts))
    return [AlertResponse.model_validate(a) for a in alerts]


@router.patch(
    "/alerts/{alert_id}",
    response_model=AlertResponse,
    status_code=status.HTTP_200_OK,
    summary="Update alert status",
    description="Allow permitted alert status changes and record an immutable audit log entry.",
)
async def update_alert_status(
    alert_id: uuid.UUID,
    payload: AlertStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AlertResponse:
    updated_alert = await owner_service.update_alert_status(
        db=db,
        alert_id=alert_id,
        new_status=payload.status,
        current_user=current_user,
        notes=payload.notes,
    )
    await db.commit()
    return AlertResponse.model_validate(updated_alert)


@router.patch(
    "/brands/{brand_id}/alerts/{alert_id}",
    response_model=AlertResponse,
    status_code=status.HTTP_200_OK,
    summary="Update alert status for brand (scoped alias)",
)
async def update_brand_scoped_alert_status(
    brand_id: uuid.UUID,
    alert_id: uuid.UUID,
    payload: AlertStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AlertResponse:
    await owner_service.verify_brand_ownership(db, brand_id, current_user)
    updated_alert = await owner_service.update_alert_status(
        db=db,
        alert_id=alert_id,
        new_status=payload.status,
        current_user=current_user,
        notes=payload.notes,
    )
    await db.commit()
    return AlertResponse.model_validate(updated_alert)


# -------------------------------------------------------------------------
# 5. Brand Asset & Metadata Management
# -------------------------------------------------------------------------
@router.patch(
    "/brands/{brand_id}",
    response_model=PublicBrandResponse,
    status_code=status.HTTP_200_OK,
    summary="Update official brand metadata",
    description="Allow authorized brand owners to manage official brand display metadata. Direct alteration of verification status is strictly rejected.",
)
async def update_brand_metadata(
    brand_id: uuid.UUID,
    payload: BrandMetadataUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PublicBrandResponse:
    # Security check: Prevent changing verification status directly
    raw_body = await request.json()
    if "verification_status" in raw_body:
        raise BadRequestError("Direct modification of brand verification status is strictly prohibited.")

    updated_brand = await owner_service.update_brand_metadata(
        db=db,
        brand_id=brand_id,
        payload=payload,
        current_user=current_user,
    )
    await db.commit()
    return PublicBrandResponse.model_validate(updated_brand)


@router.get(
    "/brands/{brand_id}/assets",
    response_model=List[BrandAssetResponse],
    status_code=status.HTTP_200_OK,
    summary="List official brand assets",
)
async def list_owner_brand_assets(
    brand_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[BrandAssetResponse]:
    await owner_service.verify_brand_ownership(db, brand_id, current_user)
    assets = await brand_service.list_brand_assets(db, brand_id, current_user)
    return [BrandAssetResponse.model_validate(a) for a in assets]


@router.post(
    "/brands/{brand_id}/assets",
    response_model=BrandAssetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register brand asset",
)
async def create_owner_brand_asset(
    brand_id: uuid.UUID,
    payload: BrandAssetCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> BrandAssetResponse:
    await owner_service.verify_brand_ownership(db, brand_id, current_user)
    asset = await brand_service.add_brand_asset(db, brand_id, payload, current_user)

    # Audit log
    await owner_service.audit_repo.create_log(
        db=db,
        actor_user_id=current_user.id,
        brand_id=brand_id,
        action="BRAND_ASSET_CREATE",
        entity_type="BRAND_ASSET",
        entity_id=str(asset.id),
        details={"asset_type": payload.asset_type.value, "storage_key": asset.storage_key},
    )
    await db.commit()
    return BrandAssetResponse.model_validate(asset)


# -------------------------------------------------------------------------
# 6. Review Management & Official Owner Replies
# -------------------------------------------------------------------------
@router.get(
    "/brands/{brand_id}/reviews",
    response_model=List[ReviewWithOwnerResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="List customer reviews with official brand responses",
    description="Retrieve customer reviews targeting the brand with pagination, moderation status, and official owner response.",
)
async def list_brand_reviews_for_owner(
    brand_id: uuid.UUID,
    response: Response,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[ReviewStatus] = Query(default=None, alias="status"),
    min_rating: Optional[int] = Query(default=None, ge=1, le=5),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[ReviewWithOwnerResponseDTO]:
    await owner_service.verify_brand_ownership(db, brand_id, current_user)
    offset = (page - 1) * page_size

    reviews = await owner_service.list_brand_reviews(
        db=db,
        brand_id=brand_id,
        limit=page_size,
        offset=offset,
        status=status_filter,
        min_rating=min_rating,
    )
    response.headers["X-Page"] = str(page)
    response.headers["X-Page-Size"] = str(page_size)
    return [
        ReviewWithOwnerResponseDTO(
            id=r.id,
            brand_id=r.brand_id,
            customer_id=r.customer_id,
            rating=r.rating,
            body=r.body,
            status=r.status,
            created_at=r.created_at,
            updated_at=r.updated_at,
            owner_response=ReviewOwnerResponseDTO.model_validate(r.owner_response) if r.owner_response else None,
        )
        for r in reviews
    ]


@router.post(
    "/brands/{brand_id}/reviews/{review_id}/respond",
    response_model=ReviewOwnerResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Respond to customer review",
    description="Publish an official brand response to a customer review using a separate ReviewResponse model. Customer reviews remain immutable.",
)
async def respond_to_customer_review(
    brand_id: uuid.UUID,
    review_id: uuid.UUID,
    payload: ReviewOwnerResponseCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ReviewOwnerResponseDTO:
    owner_reply = await owner_service.respond_to_review(
        db=db,
        brand_id=brand_id,
        review_id=review_id,
        payload=payload,
        current_user=current_user,
    )
    await db.commit()
    return ReviewOwnerResponseDTO.model_validate(owner_reply)


@router.delete(
    "/brands/{brand_id}/reviews/{review_id}",
    status_code=status.HTTP_403_FORBIDDEN,
    summary="Prohibit review deletion by brand owners",
    description="Brand owners are strictly prohibited from deleting customer reviews.",
)
async def delete_customer_review_prohibited(
    brand_id: uuid.UUID,
    review_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    raise ForbiddenError("Brand owners are strictly prohibited from deleting customer reviews.")


@router.patch(
    "/brands/{brand_id}/reviews/{review_id}",
    status_code=status.HTTP_403_FORBIDDEN,
    summary="Prohibit review rewriting by brand owners",
    description="Brand owners are strictly prohibited from rewriting customer reviews.",
)
async def rewrite_customer_review_prohibited(
    brand_id: uuid.UUID,
    review_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    raise ForbiddenError("Brand owners are strictly prohibited from rewriting customer reviews.")


# -------------------------------------------------------------------------
# 7. Audit Log Access
# -------------------------------------------------------------------------
@router.get(
    "/brands/{brand_id}/audit-logs",
    response_model=List[AuditLogResponse],
    status_code=status.HTTP_200_OK,
    summary="Get brand audit trail",
    description="Retrieve historical audit logs recording sensitive operations on this brand.",
)
async def get_brand_audit_logs(
    brand_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    action: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[AuditLogResponse]:
    await owner_service.verify_brand_ownership(db, brand_id, current_user)
    logs = await owner_service.audit_repo.list_logs_for_brand(
        db=db,
        brand_id=brand_id,
        limit=limit,
        offset=offset,
        action=action,
    )
    return [AuditLogResponse.model_validate(l) for l in logs]


# -------------------------------------------------------------------------
# 8. Visual Correlation Graph
# -------------------------------------------------------------------------
@router.get(
    "/brands/{brand_id}/graph",
    response_model=BrandGraphResponse,
    status_code=status.HTTP_200_OK,
    summary="Get threat correlation graph for brand",
    description="Retrieve node-and-edge visual graph data of correlated entities, campaigns, and defensible technical links.",
)
async def get_brand_threat_graph(
    brand_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> BrandGraphResponse:
    await owner_service.verify_brand_ownership(db, brand_id, current_user)
    graph_data = await correlation_service.get_brand_graph(db, brand_id)
    return BrandGraphResponse.model_validate(graph_data)


# -------------------------------------------------------------------------
# 9a. Correlation Trigger
# -------------------------------------------------------------------------
@router.post(
    "/brands/{brand_id}/correlate",
    response_model=CorrelationRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger threat correlation pipeline for brand",
    description=(
        "Ingests all threat report entities targeting the brand, evaluates defensible "
        "technical relationships between them, groups connected entities into campaigns, "
        "and generates deduplicated alerts. Returns a summary of entities, relationships, "
        "and campaigns produced. Only brand owners and admins may trigger this."
    ),
)
async def run_brand_correlation(
    brand_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CorrelationRunResponse:
    await owner_service.verify_brand_ownership(db, brand_id, current_user)
    result = await correlation_service.run_brand_correlation(db, brand_id)
    await db.commit()
    return CorrelationRunResponse(**result)


# -------------------------------------------------------------------------
# 9b. Campaign Detail
# -------------------------------------------------------------------------
@router.get(
    "/brands/{brand_id}/campaigns/{campaign_id}",
    response_model=CampaignResponse,
    status_code=status.HTTP_200_OK,
    summary="Get correlated threat campaign detail",
    description="Retrieve a single threat campaign with all member entities and their canonical values.",
)
async def get_campaign_detail(
    brand_id: uuid.UUID,
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    await owner_service.verify_brand_ownership(db, brand_id, current_user)
    campaign = await correlation_service.campaign_repo.get_by_id(db, campaign_id)
    if campaign is None or campaign.brand_id != brand_id:
        from app.core.exceptions import NotFoundError
        raise NotFoundError(f"Campaign '{campaign_id}' not found for brand '{brand_id}'.")
    return CampaignResponse.model_validate(campaign)


# -------------------------------------------------------------------------
# 9. Official Brand Social Assets
# -------------------------------------------------------------------------
@router.post(
    "/brands/{brand_id}/social-assets",
    response_model=SocialAssetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register official brand social asset",
    description="Register an official social media profile for a brand. Initial verification status is PENDING.",
)
async def create_social_asset(
    brand_id: uuid.UUID,
    payload: SocialAssetCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SocialAssetResponse:
    asset = await official_asset_service.register_social_asset(
        db=db,
        brand_id=brand_id,
        payload=payload,
        current_user=current_user,
    )
    return SocialAssetResponse.model_validate(asset)


@router.get(
    "/brands/{brand_id}/social-assets",
    response_model=List[SocialAssetResponse],
    status_code=status.HTTP_200_OK,
    summary="List official brand social assets",
    description="Retrieve registered official social profiles for a brand with pagination and filtering.",
)
async def list_social_assets(
    brand_id: uuid.UUID,
    response: Response,
    platform: Optional[str] = Query(default=None, description="Filter by platform"),
    verification_status: Optional[AssetVerificationStatus] = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    limit: Optional[int] = Query(default=None, ge=1, le=100),
    offset: Optional[int] = Query(default=None, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[SocialAssetResponse]:
    actual_limit = limit if limit is not None else page_size
    actual_offset = offset if offset is not None else (page - 1) * page_size

    assets, total = await official_asset_service.list_social_assets(
        db=db,
        brand_id=brand_id,
        current_user=current_user,
        platform=platform,
        status=verification_status,
        limit=actual_limit,
        offset=actual_offset,
    )
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page"] = str(page)
    response.headers["X-Page-Size"] = str(actual_limit)
    return [SocialAssetResponse.model_validate(a) for a in assets]


@router.patch(
    "/brands/{brand_id}/social-assets/{asset_id}",
    response_model=SocialAssetResponse,
    status_code=status.HTTP_200_OK,
    summary="Update official brand social asset",
    description="Update metadata for an official social asset. Verification status modifications require admin privileges.",
)
async def update_social_asset(
    brand_id: uuid.UUID,
    asset_id: uuid.UUID,
    payload: SocialAssetUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SocialAssetResponse:
    asset = await official_asset_service.update_social_asset(
        db=db,
        brand_id=brand_id,
        asset_id=asset_id,
        payload=payload,
        current_user=current_user,
    )
    return SocialAssetResponse.model_validate(asset)


@router.delete(
    "/brands/{brand_id}/social-assets/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete official brand social asset",
    description="Remove an official registered social media asset from the brand registry.",
)
async def delete_social_asset(
    brand_id: uuid.UUID,
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await official_asset_service.delete_social_asset(
        db=db,
        brand_id=brand_id,
        asset_id=asset_id,
        current_user=current_user,
    )


# -------------------------------------------------------------------------
# 10. Official Brand Mobile Applications
# -------------------------------------------------------------------------
@router.post(
    "/brands/{brand_id}/mobile-apps",
    response_model=MobileAppResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register official brand mobile application",
    description="Register an official Android or iOS mobile application. Initial verification status is PENDING.",
)
async def create_mobile_app(
    brand_id: uuid.UUID,
    payload: MobileAppCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MobileAppResponse:
    app = await official_asset_service.register_mobile_app(
        db=db,
        brand_id=brand_id,
        payload=payload,
        current_user=current_user,
    )
    return MobileAppResponse.model_validate(app)


@router.get(
    "/brands/{brand_id}/mobile-apps",
    response_model=List[MobileAppResponse],
    status_code=status.HTTP_200_OK,
    summary="List official brand mobile applications",
    description="Retrieve registered official mobile applications for a brand with pagination and filtering.",
)
async def list_mobile_apps(
    brand_id: uuid.UUID,
    response: Response,
    platform: Optional[str] = Query(default=None, description="Filter by platform (ANDROID or IOS)"),
    verification_status: Optional[AssetVerificationStatus] = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    limit: Optional[int] = Query(default=None, ge=1, le=100),
    offset: Optional[int] = Query(default=None, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[MobileAppResponse]:
    actual_limit = limit if limit is not None else page_size
    actual_offset = offset if offset is not None else (page - 1) * page_size

    apps, total = await official_asset_service.list_mobile_apps(
        db=db,
        brand_id=brand_id,
        current_user=current_user,
        platform=platform,
        status=verification_status,
        limit=actual_limit,
        offset=actual_offset,
    )
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page"] = str(page)
    response.headers["X-Page-Size"] = str(actual_limit)
    return [MobileAppResponse.model_validate(a) for a in apps]


@router.patch(
    "/brands/{brand_id}/mobile-apps/{app_id}",
    response_model=MobileAppResponse,
    status_code=status.HTTP_200_OK,
    summary="Update official brand mobile application",
    description="Update metadata for an official mobile application. Verification status modifications require admin privileges.",
)
async def update_mobile_app(
    brand_id: uuid.UUID,
    app_id: uuid.UUID,
    payload: MobileAppUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MobileAppResponse:
    app = await official_asset_service.update_mobile_app(
        db=db,
        brand_id=brand_id,
        app_id=app_id,
        payload=payload,
        current_user=current_user,
    )
    return MobileAppResponse.model_validate(app)


@router.delete(
    "/brands/{brand_id}/mobile-apps/{app_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete official brand mobile application",
    description="Remove an official registered mobile application from the brand registry.",
)
async def delete_mobile_app(
    brand_id: uuid.UUID,
    app_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await official_asset_service.delete_mobile_app(
        db=db,
        brand_id=brand_id,
        app_id=app_id,
        current_user=current_user,
    )

