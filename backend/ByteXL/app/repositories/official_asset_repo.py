from typing import List, Optional, Tuple
import uuid
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.enums import AssetVerificationStatus
from app.models.official_mobile_asset import BrandMobileApp
from app.models.official_social_asset import BrandSocialAsset


class OfficialSocialAssetRepository:
    """Data access repository for official brand social media accounts."""

    async def create(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        platform: str,
        handle: str,
        canonical_url: str,
        evidence: Optional[str] = None,
        verification_status: AssetVerificationStatus = AssetVerificationStatus.PENDING,
    ) -> BrandSocialAsset:
        asset = BrandSocialAsset(
            id=uuid.uuid4(),
            brand_id=brand_id,
            platform=platform,
            handle=handle,
            canonical_url=canonical_url,
            evidence=evidence,
            verification_status=verification_status,
        )
        db.add(asset)
        await db.flush()
        await db.refresh(asset)
        return asset

    async def get_by_id(
        self,
        db: AsyncSession,
        asset_id: uuid.UUID,
    ) -> Optional[BrandSocialAsset]:
        stmt = select(BrandSocialAsset).where(BrandSocialAsset.id == asset_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_brand_and_handle(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        platform: str,
        handle: str,
    ) -> Optional[BrandSocialAsset]:
        stmt = select(BrandSocialAsset).where(
            BrandSocialAsset.brand_id == brand_id,
            BrandSocialAsset.platform == platform,
            BrandSocialAsset.handle == handle,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_brand(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        platform: Optional[str] = None,
        status: Optional[AssetVerificationStatus] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[BrandSocialAsset], int]:
        stmt = select(BrandSocialAsset).where(BrandSocialAsset.brand_id == brand_id)
        count_stmt = select(func.count(BrandSocialAsset.id)).where(BrandSocialAsset.brand_id == brand_id)

        if platform:
            stmt = stmt.where(BrandSocialAsset.platform == platform)
            count_stmt = count_stmt.where(BrandSocialAsset.platform == platform)
        if status:
            stmt = stmt.where(BrandSocialAsset.verification_status == status)
            count_stmt = count_stmt.where(BrandSocialAsset.verification_status == status)

        stmt = stmt.order_by(desc(BrandSocialAsset.created_at)).limit(limit).offset(offset)
        
        items = list((await db.execute(stmt)).scalars().all())
        total = (await db.execute(count_stmt)).scalar() or 0
        return items, total

    async def update(
        self,
        db: AsyncSession,
        asset: BrandSocialAsset,
        canonical_url: Optional[str] = None,
        evidence: Optional[str] = None,
        verification_status: Optional[AssetVerificationStatus] = None,
    ) -> BrandSocialAsset:
        if canonical_url is not None:
            asset.canonical_url = canonical_url
        if evidence is not None:
            asset.evidence = evidence
        if verification_status is not None:
            asset.verification_status = verification_status
        await db.flush()
        await db.refresh(asset)
        return asset

    async def delete(
        self,
        db: AsyncSession,
        asset: BrandSocialAsset,
    ) -> None:
        await db.delete(asset)
        await db.flush()


class OfficialMobileAppRepository:
    """Data access repository for official brand mobile applications."""

    async def create(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        app_name: str,
        platform: str,
        app_identifier: str,
        publisher_name: str,
        store_url: str,
        evidence: Optional[str] = None,
        verification_status: AssetVerificationStatus = AssetVerificationStatus.PENDING,
    ) -> BrandMobileApp:
        app = BrandMobileApp(
            id=uuid.uuid4(),
            brand_id=brand_id,
            app_name=app_name,
            platform=platform,
            app_identifier=app_identifier,
            publisher_name=publisher_name,
            store_url=store_url,
            evidence=evidence,
            verification_status=verification_status,
        )
        db.add(app)
        await db.flush()
        await db.refresh(app)
        return app

    async def get_by_id(
        self,
        db: AsyncSession,
        app_id: uuid.UUID,
    ) -> Optional[BrandMobileApp]:
        stmt = select(BrandMobileApp).where(BrandMobileApp.id == app_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_brand_and_identifier(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        platform: str,
        app_identifier: str,
    ) -> Optional[BrandMobileApp]:
        stmt = select(BrandMobileApp).where(
            BrandMobileApp.brand_id == brand_id,
            BrandMobileApp.platform == platform,
            BrandMobileApp.app_identifier == app_identifier,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_brand(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        platform: Optional[str] = None,
        status: Optional[AssetVerificationStatus] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[BrandMobileApp], int]:
        stmt = select(BrandMobileApp).where(BrandMobileApp.brand_id == brand_id)
        count_stmt = select(func.count(BrandMobileApp.id)).where(BrandMobileApp.brand_id == brand_id)

        if platform:
            stmt = stmt.where(BrandMobileApp.platform == platform)
            count_stmt = count_stmt.where(BrandMobileApp.platform == platform)
        if status:
            stmt = stmt.where(BrandMobileApp.verification_status == status)
            count_stmt = count_stmt.where(BrandMobileApp.verification_status == status)

        stmt = stmt.order_by(desc(BrandMobileApp.created_at)).limit(limit).offset(offset)

        items = list((await db.execute(stmt)).scalars().all())
        total = (await db.execute(count_stmt)).scalar() or 0
        return items, total

    async def update(
        self,
        db: AsyncSession,
        app: BrandMobileApp,
        app_name: Optional[str] = None,
        publisher_name: Optional[str] = None,
        store_url: Optional[str] = None,
        evidence: Optional[str] = None,
        verification_status: Optional[AssetVerificationStatus] = None,
    ) -> BrandMobileApp:
        if app_name is not None:
            app.app_name = app_name
        if publisher_name is not None:
            app.publisher_name = publisher_name
        if store_url is not None:
            app.store_url = store_url
        if evidence is not None:
            app.evidence = evidence
        if verification_status is not None:
            app.verification_status = verification_status
        await db.flush()
        await db.refresh(app)
        return app

    async def delete(
        self,
        db: AsyncSession,
        app: BrandMobileApp,
    ) -> None:
        await db.delete(app)
        await db.flush()
