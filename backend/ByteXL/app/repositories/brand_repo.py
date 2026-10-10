from typing import List, Optional
import uuid
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.brand import Brand
from app.models.brand_asset import BrandAsset
from app.models.enums import AssetType, BrandVerificationStatus


def escape_like_wildcards(term: str) -> str:
    """Escape SQL LIKE special pattern characters (% and _) and backslashes."""
    return (
        term.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


class BrandRepository:
    """Data access repository for official Brand and BrandAsset records."""

    async def create(
        self,
        db: AsyncSession,
        application_id: uuid.UUID,
        owner_user_id: uuid.UUID,
        display_name: str,
        official_domain: str,
        verification_status: BrandVerificationStatus = BrandVerificationStatus.VERIFIED,
    ) -> Brand:
        """Create and persist a verified brand entity."""
        brand = Brand(
            id=uuid.uuid4(),
            application_id=application_id,
            owner_user_id=owner_user_id,
            display_name=display_name,
            official_domain=official_domain,
            verification_status=verification_status,
        )
        db.add(brand)
        await db.flush()
        await db.refresh(brand)
        return brand

    async def get_by_id(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
    ) -> Optional[Brand]:
        """Fetch brand by UUID."""
        stmt = select(Brand).where(Brand.id == brand_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_application_id(
        self,
        db: AsyncSession,
        application_id: uuid.UUID,
    ) -> Optional[Brand]:
        """Fetch brand created from specific application."""
        stmt = select(Brand).where(Brand.application_id == application_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_domain(
        self,
        db: AsyncSession,
        domain: str,
    ) -> Optional[Brand]:
        """Fetch brand by exact official domain."""
        stmt = select(Brand).where(Brand.official_domain == domain)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_public_brands(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        status: Optional[BrandVerificationStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Brand]:
        """List publicly discoverable brands with optional keyword search and status filter."""
        stmt = select(Brand).order_by(Brand.created_at.desc())
        if status:
            stmt = stmt.where(Brand.verification_status == status)
        if search:
            escaped_search = escape_like_wildcards(search.strip().lower())
            term = f"%{escaped_search}%"
            stmt = stmt.where(
                or_(
                    func.lower(Brand.display_name).like(term, escape="\\"),
                    func.lower(Brand.official_domain).like(term, escape="\\"),
                )
            )
        stmt = stmt.limit(limit).offset(offset)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def count_public_brands(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        status: Optional[BrandVerificationStatus] = None,
    ) -> int:
        """Count publicly discoverable brands matching criteria."""
        stmt = select(func.count(Brand.id))
        if status:
            stmt = stmt.where(Brand.verification_status == status)
        if search:
            escaped_search = escape_like_wildcards(search.strip().lower())
            term = f"%{escaped_search}%"
            stmt = stmt.where(
                or_(
                    func.lower(Brand.display_name).like(term, escape="\\"),
                    func.lower(Brand.official_domain).like(term, escape="\\"),
                )
            )
        result = await db.execute(stmt)
        return result.scalar() or 0

    async def get_public_brand_with_reviews(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
    ) -> Optional[Brand]:
        """Retrieve brand with eagerly loaded published reviews."""
        stmt = (
            select(Brand)
            .options(selectinload(Brand.reviews))
            .where(Brand.id == brand_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_asset(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        asset_type: AssetType,
        storage_key: str,
        content_hash: str,
    ) -> BrandAsset:
        """Store brand asset metadata."""
        asset = BrandAsset(
            id=uuid.uuid4(),
            brand_id=brand_id,
            asset_type=asset_type,
            storage_key=storage_key,
            content_hash=content_hash,
        )
        db.add(asset)
        await db.flush()
        await db.refresh(asset)
        return asset

    async def get_assets_by_brand(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
    ) -> List[BrandAsset]:
        """Retrieve all assets associated with a brand."""
        stmt = (
            select(BrandAsset)
            .where(BrandAsset.brand_id == brand_id)
            .order_by(BrandAsset.created_at.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
