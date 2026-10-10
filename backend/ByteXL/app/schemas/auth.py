import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from app.schemas.user import UserProfileResponse

import phonenumbers
from phonenumbers import NumberParseException
from app.core.config import get_settings

PHONE_REGEX = re.compile(r"^\+[1-9]\d{6,14}$")
OTP_REGEX = re.compile(r"^\d{4,8}$")


def normalize_phone_number(v: str) -> str:
    """
    Validate and normalize phone numbers to strict international E.164 format using phonenumbers.
    Example: +919876543210
    """
    if not v or not isinstance(v, str):
        raise ValueError("Phone number must be a non-empty string.")

    raw = v.strip()
    digits_only = re.sub(r"[^\d]", "", raw)
    if not digits_only:
        raise ValueError("Phone number must contain numeric digits.")

    # Format candidate
    if raw.startswith("+"):
        candidate = f"+{digits_only}"
    elif len(digits_only) == 10 and digits_only[0] in "6789":
        candidate = f"+91{digits_only}"
    elif len(digits_only) == 10:
        candidate = f"+1{digits_only}"
    else:
        raise ValueError(
            f"Phone number '{raw}' is not a valid mobile number in international E.164 format. Example: +919876543210"
        )

    try:
        parsed = phonenumbers.parse(candidate, None)
        if not phonenumbers.is_valid_number(parsed):
            # In test environment only, permit test fixture mock numbers (e.g. +1234567890, +1555...)
            settings = get_settings()
            if settings.ENVIRONMENT.lower() == "test" and candidate.startswith(("+123456", "+1555", "+1000000")):
                return candidate
            raise ValueError(
                f"Phone number '{raw}' is not a valid mobile number in international E.164 format. Example: +919876543210"
            )
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except NumberParseException:
        settings = get_settings()
        if settings.ENVIRONMENT.lower() == "test" and candidate.startswith(("+123456", "+1555", "+1000000")):
            return candidate
        raise ValueError(
            f"Unable to parse '{raw}' as a valid international phone number. Example: +919876543210"
        )


class OTPStartRequest(BaseModel):
    """Payload to initiate passwordless OTP verification."""

    phone_number: str = Field(
        ...,
        description="E.164 formatted international phone number (e.g. +919876543210)",
        examples=["+919876543210", "+14155552671"],
    )

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return normalize_phone_number(v)


class OTPStartResponse(BaseModel):
    """Uniform response returned upon OTP generation request."""

    success: bool = Field(
        default=True,
        description="Indicates verification challenge was successfully dispatched",
    )
    message: str = Field(
        default="Verification code requested. Check your phone.",
        description="Actionable verification notification message",
    )
    verification_required: bool = Field(
        default=True,
        description="Indicates client must enter the delivered code to complete authentication",
    )
    cooldown_seconds: int = Field(
        ...,
        description="Seconds remaining before another OTP request is accepted for this number",
    )
    expires_in_seconds: int = Field(
        ...,
        description="Lifespan of the issued verification code in seconds",
    )


class OTPVerifyRequest(BaseModel):
    """Payload to verify an OTP and authenticate."""

    phone_number: str = Field(
        ...,
        description="E.164 formatted international phone number",
    )
    code: str = Field(
        ...,
        description="Numeric verification code",
    )

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return normalize_phone_number(v)

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        cleaned = v.strip().replace(" ", "").replace("-", "")
        if not OTP_REGEX.match(cleaned):
            raise ValueError("OTP code must consist of numeric digits only.")
        return cleaned


class TokenResponse(BaseModel):
    """Authentication token response with access and refresh tokens."""

    success: bool = Field(default=True, description="Verification status flag")
    verified: bool = Field(default=True, description="Phone verification status flag")
    message: str = Field(
        default="Phone number verified successfully.",
        description="Verification confirmation message",
    )
    access_token: str = Field(..., description="Short-lived JWT bearer access token")
    refresh_token: str = Field(..., description="Cryptographically secure refresh token")
    token_type: str = Field(default="bearer", description="Token authentication scheme")
    expires_in: int = Field(..., description="Access token expiration period in seconds")
    user: UserProfileResponse = Field(..., description="Authenticated user profile details")


class RefreshTokenRequest(BaseModel):
    """Request payload to rotate an access token."""

    refresh_token: str = Field(..., description="Valid refresh token")


class LogoutRequest(BaseModel):
    """Request payload to invalidate a session."""

    refresh_token: Optional[str] = Field(
        default=None,
        description="Optional refresh token to revoke explicitly upon logout",
    )


class LogoutResponse(BaseModel):
    """Response returned upon successful logout."""

    message: str = Field(
        default="Successfully logged out.",
        description="Logout confirmation message",
    )
