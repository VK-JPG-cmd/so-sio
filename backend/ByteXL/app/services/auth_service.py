from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.core.exceptions import (
    AccountSuspendedError,
    AuthenticationError,
    OTPVerificationError,
    RateLimitExceededError,
)
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_otp_code,
    generate_refresh_token,
    generate_salt,
    hash_otp,
    hash_refresh_token,
    mask_phone_number,
    revoke_access_token,
    verify_otp_hash,
)
from app.models.enums import AccountStatus, UserRole
from app.models.user import User
from app.repositories.otp_repo import OTPRepository
from app.repositories.token_repo import TokenRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import TokenResponse
from app.schemas.user import UserProfileResponse
from app.services.otp_provider import get_otp_provider

logger = get_logger("app.services.auth")
settings = get_settings()


class AuthService:
    """Core domain service managing OTP passwordless authentication and token lifecycles."""

    def __init__(
        self,
        user_repo: Optional[UserRepository] = None,
        otp_repo: Optional[OTPRepository] = None,
        token_repo: Optional[TokenRepository] = None,
    ) -> None:
        self.user_repo = user_repo or UserRepository()
        self.otp_repo = otp_repo or OTPRepository()
        self.token_repo = token_repo or TokenRepository()

    async def start_otp(self, db: AsyncSession, phone_number: str) -> Tuple[int, int]:
        """
        Initiate passwordless OTP verification with rate limiting.
        Dispatches challenge via Twilio Verify (or mock provider in tests).
        Returns (cooldown_seconds, expires_in_seconds).
        """
        now = datetime.now(timezone.utc)
        masked_phone = mask_phone_number(phone_number)

        # 1. Enforce cooldown between requests (reduced in dev to 5s)
        cooldown_target = (
            5 if settings.ENVIRONMENT.lower() == "development" else settings.OTP_RESEND_COOLDOWN_SECONDS
        )
        latest = await self.otp_repo.get_latest_active(db, phone_number)
        if latest:
            created_at = latest.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            elapsed = (now - created_at).total_seconds()
            if elapsed < cooldown_target:
                remaining = int(cooldown_target - elapsed)
                logger.warning(
                    f"Rate limit cooldown triggered for {masked_phone} ({remaining}s remaining)"
                )
                raise RateLimitExceededError(
                    f"Please wait {remaining} seconds before requesting another code.",
                    details={"cooldown_seconds": remaining},
                )

        # 2. Enforce hourly cap
        one_hour_ago = now - timedelta(hours=1)
        count_last_hour = await self.otp_repo.get_recent_count(db, phone_number, one_hour_ago)
        if count_last_hour >= settings.OTP_MAX_REQUESTS_PER_HOUR:
            logger.warning(f"Hourly rate limit exceeded for {masked_phone}")
            raise RateLimitExceededError(
                "Maximum verification requests reached for this hour. Please try again later."
            )

        provider = get_otp_provider()
        expires_at = now + timedelta(seconds=settings.OTP_EXPIRATION_SECONDS)

        # Check provider type
        from app.services.otp_provider import TwilioVerifyProvider
        if isinstance(provider, TwilioVerifyProvider):
            # Twilio Verify generates and delivers the code authoritatively
            await provider.send_otp(phone_number)

            # Store audit record in repository for rate-limiting tracking
            salt = generate_salt()
            placeholder_hash = hash_otp("twilio_verify", salt)
            await self.otp_repo.create(
                db,
                phone_number=phone_number,
                hashed_code=placeholder_hash,
                salt=salt,
                expires_at=expires_at,
                max_attempts=settings.OTP_MAX_ATTEMPTS,
            )
            logger.info(f"Twilio Verify OTP challenge successfully dispatched to {masked_phone}")
        else:
            # Mock or Console provider (testing / local dev)
            code = generate_otp_code(settings.OTP_CODE_LENGTH)
            salt = generate_salt()
            hashed_code = hash_otp(code, salt)

            await self.otp_repo.create(
                db,
                phone_number=phone_number,
                hashed_code=hashed_code,
                salt=salt,
                expires_at=expires_at,
                max_attempts=settings.OTP_MAX_ATTEMPTS,
            )
            await provider.send_otp(phone_number, code)
            logger.info(f"Test OTP challenge dispatched for {masked_phone}")

        return cooldown_target, settings.OTP_EXPIRATION_SECONDS

    async def verify_otp(
        self,
        db: AsyncSession,
        phone_number: str,
        code: str,
    ) -> TokenResponse:
        """
        Verify an OTP, provision or activate the user, and issue access + refresh tokens.
        Calls Twilio Verify when configured, or verifies local cryptographic hash in tests.
        """
        now = datetime.now(timezone.utc)
        masked_phone = mask_phone_number(phone_number)
        provider = get_otp_provider()
        from app.services.otp_provider import TwilioVerifyProvider

        record = await self.otp_repo.get_latest_active(db, phone_number)
        if not record or record.is_used:
            # If using Twilio Verify, we still allow verifying against Twilio even if local session record was cleaned
            if not isinstance(provider, TwilioVerifyProvider):
                raise OTPVerificationError("No pending verification request found for this phone number.")

        if record:
            expires_at = record.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            # Check expiration
            if now > expires_at:
                logger.warning(f"Expired OTP attempt for {masked_phone}")
                raise OTPVerificationError("Verification code has expired. Please request a new code.")

            # Check attempt exhaustion
            if record.attempts_count >= record.max_attempts:
                logger.warning(f"Attempt limit exhausted for {masked_phone}")
                raise OTPVerificationError("Maximum verification attempts exceeded. Please request a new code.")

        # Verification validation
        if isinstance(provider, TwilioVerifyProvider):
            # Authoritative verification through Twilio Verify Check API
            is_valid = await provider.verify_otp(phone_number, code)
            if not is_valid:
                if record:
                    await self.otp_repo.increment_attempt(db, record)
                    await db.commit()
                logger.warning(f"Twilio Verify rejected verification code for {masked_phone}")
                raise OTPVerificationError("Invalid or expired verification code.")
        else:
            # Local constant-time hash check for testing/mock providers
            if not record or not verify_otp_hash(code, record.salt, record.hashed_code):
                if record:
                    await self.otp_repo.increment_attempt(db, record)
                    await db.commit()
                    remaining = record.max_attempts - record.attempts_count
                    logger.warning(f"Failed OTP match for {masked_phone} ({remaining} attempts remaining)")
                    if remaining <= 0:
                        raise OTPVerificationError(
                            "Invalid verification code. Maximum attempts exceeded. Please request a new code."
                        )
                    raise OTPVerificationError(
                        f"Invalid verification code. {remaining} attempt(s) remaining.",
                        details={"remaining_attempts": remaining},
                    )
                raise OTPVerificationError("Invalid or expired verification code.")

        # Success - mark OTP as consumed
        if record:
            await self.otp_repo.mark_used(db, record)

        # Resolve or create User
        user = await self.user_repo.get_by_phone(db, phone_number)
        if not user:
            logger.info(f"Provisioning new customer account for {masked_phone}")
            user = await self.user_repo.create(
                db,
                phone_number=phone_number,
                role=UserRole.CUSTOMER,
                account_status=AccountStatus.ACTIVE,
            )
        else:
            if user.account_status == AccountStatus.SUSPENDED:
                logger.warning(f"Suspended user login attempt rejected for {masked_phone}")
                raise AccountSuspendedError("Account is suspended. Access denied.")
            user = await self.user_repo.mark_verified(db, user)

        # Generate tokens
        access_token, expires_in = create_access_token(user.id, user.role.value)
        raw_refresh = generate_refresh_token()
        refresh_hash = hash_refresh_token(raw_refresh)
        refresh_expires = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

        await self.token_repo.create(
            db,
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=refresh_expires,
        )

        logger.info(f"User {user.id} ({masked_phone}) authenticated successfully")
        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
            token_type="bearer",
            expires_in=expires_in,
            user=UserProfileResponse.model_validate(user),
        )

    async def refresh_token(
        self,
        db: AsyncSession,
        raw_refresh_token: str,
    ) -> TokenResponse:
        """
        Securely rotate an expired access token using a valid refresh token.
        """
        now = datetime.now(timezone.utc)
        token_hash = hash_refresh_token(raw_refresh_token)

        token_record = await self.token_repo.get_by_hash(db, token_hash)
        if not token_record or token_record.is_revoked:
            raise AuthenticationError("Invalid or revoked refresh token.")

        expires_at = token_record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if now > expires_at:
            raise AuthenticationError("Refresh token has expired. Please log in again.")

        # Revoke old refresh token (single-use rotation policy)
        await self.token_repo.revoke(db, token_record)

        # Retrieve user
        user = await self.user_repo.get_by_id(db, token_record.user_id)
        if not user or user.account_status == AccountStatus.SUSPENDED:
            raise AccountSuspendedError("Account is suspended or invalid.")

        # Issue new token pair
        access_token, expires_in = create_access_token(user.id, user.role.value)
        new_raw_refresh = generate_refresh_token()
        new_refresh_hash = hash_refresh_token(new_raw_refresh)
        new_expires_at = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

        await self.token_repo.create(
            db,
            user_id=user.id,
            token_hash=new_refresh_hash,
            expires_at=new_expires_at,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_raw_refresh,
            token_type="bearer",
            expires_in=expires_in,
            user=UserProfileResponse.model_validate(user),
        )

    async def logout(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        raw_refresh_token: Optional[str] = None,
        raw_access_token: Optional[str] = None,
    ) -> None:
        """Revoke active refresh tokens and access token JTI for user session."""
        if raw_access_token:
            try:
                claims = decode_access_token(raw_access_token)
                jti = claims.get("jti")
                exp = claims.get("exp")
                if jti and exp:
                    revoke_access_token(jti, int(exp))
            except Exception:
                pass

        if raw_refresh_token:
            token_hash = hash_refresh_token(raw_refresh_token)
            record = await self.token_repo.get_by_hash(db, token_hash)
            if record and record.user_id == user_id:
                await self.token_repo.revoke(db, record)
                return

        # Fallback to revoking all active refresh tokens for the user
        await self.token_repo.revoke_all_for_user(db, user_id)
