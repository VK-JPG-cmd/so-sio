import base64
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
from typing import Any, List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.core.exceptions import (
    AppException,
    AuthorizationError,
    ResourceNotFoundError,
)
from app.core.logging import get_logger
from app.models.brand import Brand
from app.models.brand_application import BrandApplication
from app.models.brand_asset import BrandAsset
from app.models.domain_challenge import DomainChallenge
from app.models.enums import (
    ApplicationStatus,
    BrandVerificationStatus,
    UserRole,
)
from app.models.user import User
from app.repositories.audit_repo import AuditLogRepository
from app.repositories.brand_application_repo import BrandApplicationRepository
from app.repositories.brand_repo import BrandRepository
from app.repositories.domain_challenge_repo import DomainChallengeRepository
from app.repositories.user_repo import UserRepository
from app.schemas.brand import BrandAssetCreate
from app.schemas.brand_application import (
    AdminReviewResponse,
    BrandApplicationCreate,
    DomainChallengeResponse,
    DomainVerifyResponse,
)
from app.services.dns_resolver import get_dns_resolver

logger = get_logger("app.services.brand")
settings = get_settings()


class BrandService:
    """Core domain service managing brand applications, DNS challenge verification, and assets."""

    def __init__(
        self,
        app_repo: Optional[BrandApplicationRepository] = None,
        challenge_repo: Optional[DomainChallengeRepository] = None,
        brand_repo: Optional[BrandRepository] = None,
        user_repo: Optional[UserRepository] = None,
        audit_repo: Optional[AuditLogRepository] = None,
    ) -> None:
        self.app_repo = app_repo or BrandApplicationRepository()
        self.challenge_repo = challenge_repo or DomainChallengeRepository()
        self.brand_repo = brand_repo or BrandRepository()
        self.user_repo = user_repo or UserRepository()
        self.audit_repo = audit_repo or AuditLogRepository()

    async def create_application(
        self,
        db: AsyncSession,
        owner_user: User,
        data: BrandApplicationCreate,
    ) -> BrandApplication:
        """Submit a new brand registration application."""
        # Prevent duplicate active applications or existing verified brands
        existing_app = await self.app_repo.get_by_domain_active(db, data.official_domain)
        if existing_app:
            raise AppException(
                f"An active application for domain '{data.official_domain}' is already in progress.",
                status_code=400,
                error_code="DOMAIN_APPLICATION_EXISTS",
            )

        existing_brand = await self.brand_repo.get_by_domain(db, data.official_domain)
        if existing_brand:
            raise AppException(
                f"A verified brand for domain '{data.official_domain}' already exists.",
                status_code=400,
                error_code="BRAND_ALREADY_EXISTS",
            )

        application = await self.app_repo.create(
            db,
            owner_user_id=owner_user.id,
            business_name=data.business_name,
            official_domain=data.official_domain,
        )
        logger.info(
            f"User {owner_user.id} submitted brand application {application.id} for {data.official_domain}"
        )
        return application

    async def get_my_applications(
        self,
        db: AsyncSession,
        owner_user_id: uuid.UUID,
    ) -> List[BrandApplication]:
        """Fetch all applications belonging to the authenticated caller."""
        return await self.app_repo.get_by_owner_id(db, owner_user_id)

    async def get_application_with_ownership_check(
        self,
        db: AsyncSession,
        application_id: uuid.UUID,
        caller: User,
    ) -> BrandApplication:
        """Enforce strict ownership check before allowing operations on an application."""
        application = await self.app_repo.get_by_id(db, application_id)
        if not application:
            raise ResourceNotFoundError(f"Brand application {application_id} not found.")

        # Admins have global operational access; otherwise caller must own the application
        if caller.role != UserRole.ADMIN and application.owner_user_id != caller.id:
            logger.warning(
                f"Unauthorized cross-owner access: User {caller.id} attempted to access application {application.id} "
                f"owned by {application.owner_user_id}"
            )
            raise AuthorizationError("Access forbidden: You do not have permission to access this application.")

        return application

    async def generate_domain_challenge(
        self,
        db: AsyncSession,
        application_id: uuid.UUID,
        caller: User,
    ) -> DomainChallengeResponse:
        """Generate a cryptographically secure DNS TXT challenge for domain ownership proof."""
        application = await self.get_application_with_ownership_check(db, application_id, caller)

        if application.application_status not in (
            ApplicationStatus.PENDING_DOMAIN_VERIFICATION,
        ):
            raise AppException(
                f"Cannot generate domain challenge for application in status '{application.application_status.value}'.",
                status_code=400,
                error_code="INVALID_APPLICATION_STATUS",
            )

        now = datetime.now(timezone.utc)
        token = secrets.token_urlsafe(32)
        challenge_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        record_host = f"_brandshield-challenge.{application.official_domain}"
        expected_value = f"brandshield-verification={token}"
        expires_at = now + timedelta(hours=settings.DOMAIN_CHALLENGE_EXPIRE_HOURS)

        await self.challenge_repo.create(
            db,
            application_id=application.id,
            challenge_hash=challenge_hash,
            record_host=record_host,
            expires_at=expires_at,
            max_attempts=settings.DOMAIN_CHALLENGE_MAX_ATTEMPTS,
        )

        logger.info(f"Generated domain challenge for application {application.id} ({record_host})")

        return DomainChallengeResponse(
            application_id=application.id,
            domain=application.official_domain,
            record_type="TXT",
            record_host=record_host,
            challenge_token=token,
            expected_record_value=expected_value,
            expires_at=expires_at,
        )

    async def verify_domain(
        self,
        db: AsyncSession,
        application_id: uuid.UUID,
        token: str,
        caller: User,
    ) -> DomainVerifyResponse:
        """
        Verify domain ownership by querying actual DNS TXT records.
        Never relies on client assertions or basic IP resolution.
        """
        application = await self.get_application_with_ownership_check(db, application_id, caller)

        if application.application_status != ApplicationStatus.PENDING_DOMAIN_VERIFICATION:
            raise AppException(
                f"Application is in status '{application.application_status.value}'. Domain verification not allowed.",
                status_code=400,
                error_code="INVALID_APPLICATION_STATUS",
            )

        challenge = await self.challenge_repo.get_latest_for_application(db, application.id)
        if not challenge:
            raise AppException(
                "No active domain challenge exists for this application. Please generate a challenge first.",
                status_code=400,
                error_code="CHALLENGE_NOT_FOUND",
            )

        now = datetime.now(timezone.utc)
        expires_at = challenge.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        # 1. Enforce challenge expiration
        if now > expires_at:
            logger.warning(f"Domain challenge expired for application {application.id}")
            raise AppException(
                "Domain challenge has expired. Please generate a fresh challenge.",
                status_code=400,
                error_code="CHALLENGE_EXPIRED",
            )

        # 2. Enforce attempt limits
        if challenge.attempts_count >= challenge.max_attempts:
            logger.warning(f"Verification attempts exhausted for application {application.id}")
            raise AppException(
                "Maximum verification attempts exceeded. Please generate a new challenge.",
                status_code=400,
                error_code="ATTEMPTS_EXHAUSTED",
            )

        # 3. Verify token matches stored challenge hash
        provided_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        if not hmac.compare_digest(provided_hash, challenge.challenge_hash):
            await self.challenge_repo.increment_attempt(db, challenge)
            remaining = challenge.max_attempts - challenge.attempts_count
            logger.warning(f"Challenge token mismatch for application {application.id} ({remaining} attempts left)")
            raise AppException(
                f"Invalid challenge token. {remaining} attempt(s) remaining.",
                status_code=400,
                error_code="CHALLENGE_MISMATCH",
                details={"remaining_attempts": remaining},
            )

        # 4. Perform authentic DNS TXT query
        expected_txt = f"brandshield-verification={token}"
        resolver = get_dns_resolver()
        txt_records = await resolver.query_txt_records(challenge.record_host)

        matched = any(expected_txt in record for record in txt_records)
        if not matched:
            await self.challenge_repo.increment_attempt(db, challenge)
            remaining = challenge.max_attempts - challenge.attempts_count
            logger.warning(
                f"DNS TXT record '{expected_txt}' not found on {challenge.record_host}. {remaining} attempts left."
            )
            raise AppException(
                f"DNS verification failed: TXT record matching '{expected_txt}' was not detected at {challenge.record_host}. "
                f"Ensure DNS propagation and try again. {remaining} attempt(s) remaining.",
                status_code=400,
                error_code="DNS_RECORD_NOT_FOUND",
                details={"queried_host": challenge.record_host, "remaining_attempts": remaining},
            )

        # 5. Success - mark challenge verified and transition application to PENDING_REVIEW
        await self.challenge_repo.mark_verified(db, challenge)
        await self.app_repo.update_status(db, application, ApplicationStatus.PENDING_REVIEW)

        logger.info(
            f"Domain ownership for {application.official_domain} verified successfully. Application {application.id} moved to PENDING_REVIEW."
        )

        return DomainVerifyResponse(
            application_id=application.id,
            official_domain=application.official_domain,
            verified=True,
            application_status=ApplicationStatus.PENDING_REVIEW,
            message="Domain ownership successfully verified. Application forwarded for administrative review.",
            verified_at=challenge.verified_at,
        )

    async def admin_review(
        self,
        db: AsyncSession,
        application_id: uuid.UUID,
        decision: str,
        admin_user: User,
        notes: Optional[str] = None,
    ) -> AdminReviewResponse:
        """Administrative review workflow to approve or reject a brand application."""
        application = await self.app_repo.get_by_id(db, application_id)
        if not application:
            raise ResourceNotFoundError(f"Brand application {application_id} not found.")

        if application.application_status in (ApplicationStatus.APPROVED, ApplicationStatus.REJECTED):
            raise AppException(
                f"Application is already finalized in status '{application.application_status.value}'.",
                status_code=400,
                error_code="APPLICATION_ALREADY_FINALIZED",
            )

        now = datetime.now(timezone.utc)

        if decision.upper() == "APPROVE":
            # Update application status
            await self.app_repo.update_status(
                db, application, ApplicationStatus.APPROVED, reviewed_at=now
            )

            # Create or activate Brand profile
            brand = await self.brand_repo.create(
                db,
                application_id=application.id,
                owner_user_id=application.owner_user_id,
                display_name=application.business_name,
                official_domain=application.official_domain,
                verification_status=BrandVerificationStatus.VERIFIED,
            )

            # Upgrade applicant's role from CUSTOMER to BRAND_OWNER if needed
            owner = await self.user_repo.get_by_id(db, application.owner_user_id)
            if owner and owner.role == UserRole.CUSTOMER:
                owner.role = UserRole.BRAND_OWNER
                await db.flush()

            # Record immutable administrative audit log
            await self.audit_repo.create_log(
                db=db,
                actor_user_id=admin_user.id,
                action="ADMIN_APPLICATION_APPROVE",
                entity_type="BRAND_APPLICATION",
                entity_id=str(application.id),
                details={
                    "brand_id": str(brand.id),
                    "official_domain": application.official_domain,
                    "notes": notes,
                },
                brand_id=brand.id,
            )

            logger.info(f"Admin {admin_user.id} APPROVED application {application.id}. Brand {brand.id} created.")
            return AdminReviewResponse(
                application_id=application.id,
                application_status=ApplicationStatus.APPROVED,
                reviewed_at=now,
                brand_id=brand.id,
                message="Brand application approved and official Brand profile created.",
            )
        else:
            await self.app_repo.update_status(
                db, application, ApplicationStatus.REJECTED, reviewed_at=now
            )

            # Record immutable administrative audit log
            await self.audit_repo.create_log(
                db=db,
                actor_user_id=admin_user.id,
                action="ADMIN_APPLICATION_REJECT",
                entity_type="BRAND_APPLICATION",
                entity_id=str(application.id),
                details={
                    "official_domain": application.official_domain,
                    "notes": notes,
                },
            )

            logger.info(f"Admin {admin_user.id} REJECTED application {application.id}.")
            return AdminReviewResponse(
                application_id=application.id,
                application_status=ApplicationStatus.REJECTED,
                reviewed_at=now,
                brand_id=None,
                message="Brand application was rejected.",
            )

    async def list_public_brands(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        status: Optional[BrandVerificationStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Brand]:
        """Discover public brands with optional search keyword and status filtering."""
        return await self.brand_repo.list_public_brands(
            db, search=search, status=status, limit=limit, offset=offset
        )

    async def count_public_brands(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        status: Optional[BrandVerificationStatus] = None,
    ) -> int:
        """Count public brands matching criteria."""
        return await self.brand_repo.count_public_brands(db, search=search, status=status)

    async def get_public_brand_by_id(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
    ) -> Brand:
        """Retrieve single public brand profile."""
        brand = await self.brand_repo.get_by_id(db, brand_id)
        if not brand:
            raise ResourceNotFoundError(f"Brand {brand_id} not found.")
        return brand

    async def get_public_brand_detail(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
    ) -> Tuple[Brand, List[Any]]:
        """Retrieve single public brand profile along with approved published reviews."""
        from app.models.enums import ReviewStatus
        brand = await self.brand_repo.get_public_brand_with_reviews(db, brand_id)
        if not brand:
            raise ResourceNotFoundError(f"Brand {brand_id} not found.")
        published_reviews = [r for r in brand.reviews if r.status == ReviewStatus.PUBLISHED]
        return brand, published_reviews

    async def add_brand_asset(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        data: BrandAssetCreate,
        caller: User,
    ) -> BrandAsset:
        """Register official brand asset with content hashing and secure storage key."""
        brand = await self.brand_repo.get_by_id(db, brand_id)
        if not brand:
            raise ResourceNotFoundError(f"Brand {brand_id} not found.")

        if caller.role != UserRole.ADMIN and brand.owner_user_id != caller.id:
            raise AuthorizationError("Access forbidden: You do not own this brand.")

        # Decode content and compute content hash
        raw_bytes = base64.b64decode(data.content_base64)
        content_hash = hashlib.sha256(raw_bytes).hexdigest()

        # Generate non-traversable safe storage key
        asset_uuid = uuid.uuid4()
        storage_key = f"brands/{brand_id}/assets/{asset_uuid}_{data.filename}"

        asset = await self.brand_repo.create_asset(
            db,
            brand_id=brand.id,
            asset_type=data.asset_type,
            storage_key=storage_key,
            content_hash=content_hash,
        )

        logger.info(f"Registered asset {asset.id} for brand {brand.id} [key={storage_key}]")
        return asset

    async def list_brand_assets(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        caller: User,
    ) -> List[BrandAsset]:
        """List assets belonging to a brand."""
        brand = await self.brand_repo.get_by_id(db, brand_id)
        if not brand:
            raise ResourceNotFoundError(f"Brand {brand_id} not found.")

        if caller.role != UserRole.ADMIN and brand.owner_user_id != caller.id:
            raise AuthorizationError("Access forbidden: You do not own this brand.")

        return await self.brand_repo.get_assets_by_brand(db, brand.id)
