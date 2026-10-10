"""
Authoritative Brand Intelligence Service.
Retrieves and indexes verified brand metadata.
Strict Invariant: Only verified brand profiles are treated as authoritative reference data.
"""

from typing import Dict, List, Optional, Set
import uuid
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.logging import get_logger
from app.models.brand import Brand
from app.models.brand_asset import BrandAsset
from app.models.enums import AssetType, AssetVerificationStatus, BrandVerificationStatus

logger = get_logger("app.services.detection.brand_intelligence")


class OfficialSocialAccountProfile(BaseModel):
    """Authoritative metadata for a brand's registered official social profile."""

    id: uuid.UUID
    platform: str
    handle: str
    canonical_url: str
    verification_status: str
    is_verified: bool = False


class OfficialMobileAppProfile(BaseModel):
    """Authoritative metadata for a brand's registered official mobile application."""

    id: uuid.UUID
    app_name: str
    platform: str
    app_identifier: str
    publisher_name: str
    store_url: str
    verification_status: str
    is_verified: bool = False


class VerifiedBrandProfile(BaseModel):
    """Authoritative digital profile containing validated, official brand assets."""

    brand_id: uuid.UUID
    display_name: str
    official_domain: str
    known_names: List[str] = Field(default_factory=list)
    known_social_handles: List[str] = Field(default_factory=list)
    approved_keywords: List[str] = Field(default_factory=list)
    logo_storage_keys: List[str] = Field(default_factory=list)
    logo_hashes: List[str] = Field(default_factory=list)
    official_social_accounts: List[OfficialSocialAccountProfile] = Field(default_factory=list)
    official_mobile_apps: List[OfficialMobileAppProfile] = Field(default_factory=list)


class BrandIntelligenceService:
    """Service to load and query verified brand reference intelligence."""

    def __init__(self) -> None:
        pass

    def extract_keywords_from_name(self, name: str) -> Set[str]:
        """Derive authoritative brand keywords from verified brand title."""
        tokens = [t.strip().lower() for t in name.split() if len(t.strip()) > 2]
        # Remove common corporate suffixes
        stopwords = {"inc", "inc.", "llc", "ltd", "corp", "corporation", "co", "company"}
        return {t for t in tokens if t not in stopwords}

    async def get_verified_brand(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
    ) -> Optional[VerifiedBrandProfile]:
        """
        Fetch a single verified brand profile.
        Returns None if brand does not exist or is not VERIFIED.
        """
        stmt = (
            select(Brand)
            .options(
                selectinload(Brand.assets),
                selectinload(Brand.social_assets),
                selectinload(Brand.mobile_apps),
            )
            .where(
                Brand.id == brand_id,
                Brand.verification_status == BrandVerificationStatus.VERIFIED,
            )
        )
        result = await db.execute(stmt)
        brand = result.scalar_one_or_none()
        if not brand:
            logger.info(f"Brand {brand_id} is not verified or not found. Reference intelligence denied.")
            return None

        return self._build_verified_profile(brand)

    async def get_verified_brand_by_domain(
        self,
        db: AsyncSession,
        domain: str,
    ) -> Optional[VerifiedBrandProfile]:
        """Fetch verified brand profile by canonical official domain."""
        canonical_domain = domain.strip().lower()
        stmt = (
            select(Brand)
            .options(
                selectinload(Brand.assets),
                selectinload(Brand.social_assets),
                selectinload(Brand.mobile_apps),
            )
            .where(
                Brand.official_domain == canonical_domain,
                Brand.verification_status == BrandVerificationStatus.VERIFIED,
            )
        )
        result = await db.execute(stmt)
        brand = result.scalar_one_or_none()
        if not brand:
            return None

        return self._build_verified_profile(brand)

    async def list_all_verified_brands(
        self,
        db: AsyncSession,
    ) -> List[VerifiedBrandProfile]:
        """Retrieve all currently verified brand profiles for detection matching."""
        stmt = (
            select(Brand)
            .options(
                selectinload(Brand.assets),
                selectinload(Brand.social_assets),
                selectinload(Brand.mobile_apps),
            )
            .where(Brand.verification_status == BrandVerificationStatus.VERIFIED)
        )
        result = await db.execute(stmt)
        brands = result.scalars().all()
        return [self._build_verified_profile(b) for b in brands]

    async def get_verified_brands(
        self,
        db: AsyncSession,
    ) -> List[VerifiedBrandProfile]:
        """Alias for list_all_verified_brands."""
        return await self.list_all_verified_brands(db)

    def _build_verified_profile(self, brand: Brand) -> VerifiedBrandProfile:
        """Construct authoritative reference profile from validated DB entity."""
        keywords = self.extract_keywords_from_name(brand.display_name)
        # Also include the SLD from the domain as an authoritative keyword
        domain_parts = brand.official_domain.split(".")
        if domain_parts:
            sld = domain_parts[0].lower()
            if len(sld) > 2:
                keywords.add(sld)

        # Collect logo assets
        logo_keys = []
        logo_hashes = []
        for asset in getattr(brand, "assets", []):
            if asset.asset_type in (AssetType.LOGO, AssetType.ICON):
                logo_keys.append(asset.storage_key)
                logo_hashes.append(asset.content_hash)

        # Build official handles
        # Normalize handle from brand name
        clean_name_handle = brand.display_name.lower().replace(" ", "").replace("-", "")
        handles = [clean_name_handle]

        # Collect official social accounts
        social_profiles: List[OfficialSocialAccountProfile] = []
        for sa in getattr(brand, "social_assets", []):
            status_val = sa.verification_status.value if hasattr(sa.verification_status, "value") else str(sa.verification_status)
            is_ver = (status_val == AssetVerificationStatus.VERIFIED.value)
            social_profiles.append(
                OfficialSocialAccountProfile(
                    id=sa.id,
                    platform=sa.platform,
                    handle=sa.handle,
                    canonical_url=sa.canonical_url,
                    verification_status=status_val,
                    is_verified=is_ver,
                )
            )
            if is_ver:
                clean_h = sa.handle.lower().lstrip("@").strip()
                if clean_h and clean_h not in handles:
                    handles.append(clean_h)

        # Collect official mobile apps
        mobile_profiles: List[OfficialMobileAppProfile] = []
        for ma in getattr(brand, "mobile_apps", []):
            status_val = ma.verification_status.value if hasattr(ma.verification_status, "value") else str(ma.verification_status)
            is_ver = (status_val == AssetVerificationStatus.VERIFIED.value)
            mobile_profiles.append(
                OfficialMobileAppProfile(
                    id=ma.id,
                    app_name=ma.app_name,
                    platform=ma.platform,
                    app_identifier=ma.app_identifier,
                    publisher_name=ma.publisher_name,
                    store_url=ma.store_url,
                    verification_status=status_val,
                    is_verified=is_ver,
                )
            )

        return VerifiedBrandProfile(
            brand_id=brand.id,
            display_name=brand.display_name,
            official_domain=brand.official_domain,
            known_names=[brand.display_name],
            known_social_handles=handles,
            approved_keywords=sorted(list(keywords)),
            logo_storage_keys=logo_keys,
            logo_hashes=logo_hashes,
            official_social_accounts=social_profiles,
            official_mobile_apps=mobile_profiles,
        )
