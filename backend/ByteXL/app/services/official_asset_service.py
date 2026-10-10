from typing import List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.models.enums import AssetVerificationStatus, UserRole
from app.models.official_mobile_asset import BrandMobileApp
from app.models.official_social_asset import BrandSocialAsset
from app.models.user import User
from app.repositories.audit_repo import AuditLogRepository
from app.repositories.official_asset_repo import (
    OfficialMobileAppRepository,
    OfficialSocialAssetRepository,
)
from app.schemas.official_assets import (
    MobileAppCreate,
    MobileAppUpdate,
    SocialAssetCreate,
    SocialAssetUpdate,
)
from app.services.owner_portal_service import OwnerPortalService

logger = get_logger("app.services.official_assets")


class OfficialAssetService:
    """Domain service managing official brand social accounts and mobile applications."""

    def __init__(self) -> None:
        self.social_repo = OfficialSocialAssetRepository()
        self.mobile_repo = OfficialMobileAppRepository()
        self.owner_service = OwnerPortalService()
        self.audit_repo = AuditLogRepository()

    # -------------------------------------------------------------------------
    # Social Accounts
    # -------------------------------------------------------------------------
    async def register_social_asset(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        payload: SocialAssetCreate,
        current_user: User,
    ) -> BrandSocialAsset:
        """Register an official social media account. Initial status is PENDING."""
        await self.owner_service.verify_brand_ownership(db, brand_id, current_user)

        # Check duplicate
        existing = await self.social_repo.get_by_brand_and_handle(
            db=db,
            brand_id=brand_id,
            platform=payload.platform,
            handle=payload.handle,
        )
        if existing:
            raise BadRequestError(
                f"An official social account for platform '{payload.platform}' and handle '{payload.handle}' is already registered for this brand."
            )

        asset = await self.social_repo.create(
            db=db,
            brand_id=brand_id,
            platform=payload.platform,
            handle=payload.handle,
            canonical_url=payload.canonical_url,
            evidence=payload.evidence,
            verification_status=AssetVerificationStatus.PENDING,
        )

        await self.audit_repo.create_log(
            db=db,
            actor_user_id=current_user.id,
            brand_id=brand_id,
            action="OFFICIAL_SOCIAL_ASSET_REGISTERED",
            entity_type="BRAND_SOCIAL_ASSET",
            entity_id=str(asset.id),
            details={
                "platform": asset.platform,
                "handle": asset.handle,
                "canonical_url": asset.canonical_url,
                "status": asset.verification_status.value,
            },
        )
        return asset

    async def list_social_assets(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        current_user: User,
        platform: Optional[str] = None,
        status: Optional[AssetVerificationStatus] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[BrandSocialAsset], int]:
        await self.owner_service.verify_brand_ownership(db, brand_id, current_user)
        return await self.social_repo.list_by_brand(
            db=db,
            brand_id=brand_id,
            platform=platform,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def get_social_asset(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        asset_id: uuid.UUID,
        current_user: User,
    ) -> BrandSocialAsset:
        await self.owner_service.verify_brand_ownership(db, brand_id, current_user)
        asset = await self.social_repo.get_by_id(db, asset_id)
        if not asset or asset.brand_id != brand_id:
            raise NotFoundError(f"Social asset '{asset_id}' not found for brand '{brand_id}'.")
        return asset

    async def update_social_asset(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        asset_id: uuid.UUID,
        payload: SocialAssetUpdate,
        current_user: User,
    ) -> BrandSocialAsset:
        await self.owner_service.verify_brand_ownership(db, brand_id, current_user)
        asset = await self.social_repo.get_by_id(db, asset_id)
        if not asset or asset.brand_id != brand_id:
            raise NotFoundError(f"Social asset '{asset_id}' not found for brand '{brand_id}'.")

        # Only admins can update verification status
        if payload.verification_status is not None and payload.verification_status != asset.verification_status:
            if current_user.role != UserRole.ADMIN:
                raise ForbiddenError("Only platform administrators can modify asset verification status.")

        updated = await self.social_repo.update(
            db=db,
            asset=asset,
            canonical_url=payload.canonical_url,
            evidence=payload.evidence,
            verification_status=payload.verification_status,
        )

        await self.audit_repo.create_log(
            db=db,
            actor_user_id=current_user.id,
            brand_id=brand_id,
            action="OFFICIAL_SOCIAL_ASSET_UPDATED",
            entity_type="BRAND_SOCIAL_ASSET",
            entity_id=str(updated.id),
            details={
                "canonical_url": updated.canonical_url,
                "status": updated.verification_status.value,
            },
        )
        return updated

    async def delete_social_asset(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        asset_id: uuid.UUID,
        current_user: User,
    ) -> None:
        await self.owner_service.verify_brand_ownership(db, brand_id, current_user)
        asset = await self.social_repo.get_by_id(db, asset_id)
        if not asset or asset.brand_id != brand_id:
            raise NotFoundError(f"Social asset '{asset_id}' not found for brand '{brand_id}'.")

        await self.social_repo.delete(db, asset)
        await self.audit_repo.create_log(
            db=db,
            actor_user_id=current_user.id,
            brand_id=brand_id,
            action="OFFICIAL_SOCIAL_ASSET_DELETED",
            entity_type="BRAND_SOCIAL_ASSET",
            entity_id=str(asset_id),
            details={"platform": asset.platform, "handle": asset.handle},
        )

    # -------------------------------------------------------------------------
    # Mobile Applications
    # -------------------------------------------------------------------------
    async def register_mobile_app(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        payload: MobileAppCreate,
        current_user: User,
    ) -> BrandMobileApp:
        """Register an official mobile application. Never executes APKs."""
        await self.owner_service.verify_brand_ownership(db, brand_id, current_user)

        # Check duplicate
        existing = await self.mobile_repo.get_by_brand_and_identifier(
            db=db,
            brand_id=brand_id,
            platform=payload.platform,
            app_identifier=payload.app_identifier,
        )
        if existing:
            raise BadRequestError(
                f"An official mobile application for platform '{payload.platform}' and identifier '{payload.app_identifier}' is already registered for this brand."
            )

        app = await self.mobile_repo.create(
            db=db,
            brand_id=brand_id,
            app_name=payload.app_name,
            platform=payload.platform,
            app_identifier=payload.app_identifier,
            publisher_name=payload.publisher_name,
            store_url=payload.store_url,
            evidence=payload.evidence,
            verification_status=AssetVerificationStatus.PENDING,
        )

        await self.audit_repo.create_log(
            db=db,
            actor_user_id=current_user.id,
            brand_id=brand_id,
            action="OFFICIAL_MOBILE_APP_REGISTERED",
            entity_type="BRAND_MOBILE_APP",
            entity_id=str(app.id),
            details={
                "app_name": app.app_name,
                "platform": app.platform,
                "app_identifier": app.app_identifier,
                "publisher_name": app.publisher_name,
                "status": app.verification_status.value,
            },
        )
        return app

    async def list_mobile_apps(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        current_user: User,
        platform: Optional[str] = None,
        status: Optional[AssetVerificationStatus] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[BrandMobileApp], int]:
        await self.owner_service.verify_brand_ownership(db, brand_id, current_user)
        return await self.mobile_repo.list_by_brand(
            db=db,
            brand_id=brand_id,
            platform=platform,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def get_mobile_app(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        app_id: uuid.UUID,
        current_user: User,
    ) -> BrandMobileApp:
        await self.owner_service.verify_brand_ownership(db, brand_id, current_user)
        app = await self.mobile_repo.get_by_id(db, app_id)
        if not app or app.brand_id != brand_id:
            raise NotFoundError(f"Mobile application '{app_id}' not found for brand '{brand_id}'.")
        return app

    async def update_mobile_app(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        app_id: uuid.UUID,
        payload: MobileAppUpdate,
        current_user: User,
    ) -> BrandMobileApp:
        await self.owner_service.verify_brand_ownership(db, brand_id, current_user)
        app = await self.mobile_repo.get_by_id(db, app_id)
        if not app or app.brand_id != brand_id:
            raise NotFoundError(f"Mobile application '{app_id}' not found for brand '{brand_id}'.")

        # Only admins can update verification status
        if payload.verification_status is not None and payload.verification_status != app.verification_status:
            if current_user.role != UserRole.ADMIN:
                raise ForbiddenError("Only platform administrators can modify asset verification status.")

        updated = await self.mobile_repo.update(
            db=db,
            app=app,
            app_name=payload.app_name,
            publisher_name=payload.publisher_name,
            store_url=payload.store_url,
            evidence=payload.evidence,
            verification_status=payload.verification_status,
        )

        await self.audit_repo.create_log(
            db=db,
            actor_user_id=current_user.id,
            brand_id=brand_id,
            action="OFFICIAL_MOBILE_APP_UPDATED",
            entity_type="BRAND_MOBILE_APP",
            entity_id=str(updated.id),
            details={
                "app_name": updated.app_name,
                "status": updated.verification_status.value,
            },
        )
        return updated

    async def delete_mobile_app(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        app_id: uuid.UUID,
        current_user: User,
    ) -> None:
        await self.owner_service.verify_brand_ownership(db, brand_id, current_user)
        app = await self.mobile_repo.get_by_id(db, app_id)
        if not app or app.brand_id != brand_id:
            raise NotFoundError(f"Mobile application '{app_id}' not found for brand '{brand_id}'.")

        await self.mobile_repo.delete(db, app)
        await self.audit_repo.create_log(
            db=db,
            actor_user_id=current_user.id,
            brand_id=brand_id,
            action="OFFICIAL_MOBILE_APP_DELETED",
            entity_type="BRAND_MOBILE_APP",
            entity_id=str(app_id),
            details={"platform": app.platform, "app_identifier": app.app_identifier},
        )
