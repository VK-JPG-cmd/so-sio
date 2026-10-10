from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    LogoutRequest,
    LogoutResponse,
    OTPStartRequest,
    OTPStartResponse,
    OTPVerifyRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from app.core.config import get_settings
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()
settings = get_settings()


@router.post(
    "/otp/send",
    response_model=OTPStartResponse,
    status_code=status.HTTP_200_OK,
    summary="Request OTP verification code",
    description=(
        "Initiate passwordless login or registration. Dispatches a verification challenge "
        "via Twilio Verify SMS to the provided phone number."
    ),
)
@router.post(
    "/otp/start",
    response_model=OTPStartResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=True,
    summary="Request OTP verification code (alias)",
)
async def start_otp(
    payload: OTPStartRequest,
    db: AsyncSession = Depends(get_db),
) -> OTPStartResponse:
    cooldown, expires_in = await auth_service.start_otp(db, payload.phone_number)
    return OTPStartResponse(
        success=True,
        message="Verification code requested. Check your phone.",
        verification_required=True,
        cooldown_seconds=cooldown,
        expires_in_seconds=expires_in,
    )


from app.core.rate_limit import rate_limit


@router.post(
    "/otp/verify",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(rate_limit(requests_limit=30, window_seconds=60))],
    summary="Verify OTP and obtain JWT tokens",
    description=(
        "Verifies the submitted numeric OTP code. If valid, provisions or marks "
        "the account as verified, and issues short-lived access and refresh tokens."
    ),
)
async def verify_otp(
    payload: OTPVerifyRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    return await auth_service.verify_otp(db, payload.phone_number, payload.code)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotate refresh token and issue new access token",
    description="Rotates the single-use refresh token and issues a fresh access token pair.",
)
async def refresh_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    return await auth_service.refresh_token(db, payload.refresh_token)


from typing import Optional
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer_scheme = HTTPBearer(auto_error=False)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Log out and invalidate tokens",
    description="Revokes the active refresh token and access token JTI for the authenticated user session.",
)
async def logout(
    payload: LogoutRequest = LogoutRequest(),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LogoutResponse:
    raw_access = credentials.credentials if credentials else None
    await auth_service.logout(
        db,
        user_id=current_user.id,
        raw_refresh_token=payload.refresh_token,
        raw_access_token=raw_access,
    )
    return LogoutResponse(message="Successfully logged out.")
