from datetime import datetime
import re
from typing import Optional
from urllib.parse import urlparse
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.core.exceptions import ValidationError
from app.models.enums import AssetVerificationStatus, MobilePlatform, SocialPlatform

ANDROID_PACKAGE_REGEX = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)+$")
IOS_IDENTIFIER_REGEX = re.compile(r"^(?:id\d+|\d+|[a-zA-Z0-9_-]+(?:\.[a-zA-Z0-9_-]+)+)$")

PLATFORM_HOST_MAP = {
    SocialPlatform.X: {"x.com", "twitter.com"},
    SocialPlatform.INSTAGRAM: {"instagram.com"},
    SocialPlatform.FACEBOOK: {"facebook.com", "fb.com"},
    SocialPlatform.LINKEDIN: {"linkedin.com"},
    SocialPlatform.YOUTUBE: {"youtube.com", "youtu.be"},
    SocialPlatform.TIKTOK: {"tiktok.com"},
    SocialPlatform.TELEGRAM: {"t.me", "telegram.me", "telegram.org"},
}


class SocialAssetCreate(BaseModel):
    """Payload to register an official social media account for a brand."""

    platform: str = Field(..., description="Target platform label (e.g. X, Instagram, LinkedIn, Telegram)")
    handle: str = Field(..., min_length=1, max_length=100, description="Username or account handle")
    canonical_url: str = Field(..., min_length=5, max_length=512, description="Canonical profile URL")
    evidence: Optional[str] = Field(None, max_length=1024, description="Optional supporting reference or verification proof")

    @field_validator("platform", mode="before")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValidationError("Platform is required.")
        norm = v.strip().upper()
        if norm == "TWITTER":
            norm = "X"
        valid_platforms = {p.value for p in SocialPlatform}
        if norm not in valid_platforms:
            raise ValidationError(
                f"Invalid platform '{v}'. Must be one of: {', '.join(sorted(valid_platforms))}."
            )
        return norm

    @field_validator("handle", mode="before")
    @classmethod
    def normalize_handle(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValidationError("Account handle is required.")
        norm = v.strip().lstrip("@").strip().lower()
        if not norm:
            raise ValidationError("Account handle cannot be empty.")
        return norm

    @field_validator("canonical_url")
    @classmethod
    def validate_url(cls, v: str, info) -> str:
        if not v or not isinstance(v, str):
            raise ValidationError("Canonical profile URL is required.")
        parsed = urlparse(v.strip())
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValidationError("Canonical profile URL must be a valid HTTP/HTTPS URL.")
        
        # Check platform-specific host if available
        platform_str = info.data.get("platform")
        if platform_str:
            try:
                platform_enum = SocialPlatform(platform_str)
                allowed_hosts = PLATFORM_HOST_MAP.get(platform_enum)
                if allowed_hosts:
                    host = parsed.netloc.lower()
                    if ":" in host:
                        host = host.split(":")[0]
                    matched = any(host == ah or host.endswith("." + ah) for ah in allowed_hosts)
                    if not matched:
                        raise ValidationError(
                            f"Canonical URL host '{host}' does not match expected domains for platform {platform_str}."
                        )
            except ValueError:
                pass
        return v.strip()


class SocialAssetUpdate(BaseModel):
    """Payload to update an official social media account."""

    canonical_url: Optional[str] = Field(None, min_length=5, max_length=512)
    evidence: Optional[str] = Field(None, max_length=1024)
    verification_status: Optional[AssetVerificationStatus] = None

    @field_validator("canonical_url")
    @classmethod
    def validate_update_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        parsed = urlparse(v.strip())
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValidationError("Canonical profile URL must be a valid HTTP/HTTPS URL.")
        return v.strip()


class SocialAssetResponse(BaseModel):
    """Response schema for official brand social assets."""

    id: uuid.UUID
    brand_id: uuid.UUID
    platform: str
    handle: str
    canonical_url: str
    verification_status: AssetVerificationStatus
    evidence: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MobileAppCreate(BaseModel):
    """Payload to register an official mobile application for a brand."""

    app_name: str = Field(..., min_length=1, max_length=255, description="Official application title")
    platform: str = Field(..., description="Mobile platform (ANDROID or IOS)")
    app_identifier: str = Field(..., min_length=2, max_length=255, description="Package name or bundle/app identifier")
    publisher_name: str = Field(..., min_length=1, max_length=255, description="Official publisher or developer entity")
    store_url: str = Field(..., min_length=5, max_length=512, description="Store listing URL")
    evidence: Optional[str] = Field(None, max_length=1024, description="Optional verification proof")

    @field_validator("app_name", mode="before")
    @classmethod
    def validate_app_name(cls, v: str) -> str:
        if not v or not isinstance(v, str) or not v.strip():
            raise ValidationError("Application name cannot be empty.")
        return v.strip()

    @field_validator("platform", mode="before")
    @classmethod
    def validate_mobile_platform(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValidationError("Mobile platform is required.")
        norm = v.strip().upper()
        if norm not in (MobilePlatform.ANDROID.value, MobilePlatform.IOS.value):
            raise ValidationError(f"Invalid mobile platform '{v}'. Must be 'ANDROID' or 'IOS'.")
        return norm

    @field_validator("publisher_name", mode="before")
    @classmethod
    def validate_publisher(cls, v: str) -> str:
        if not v or not isinstance(v, str) or not v.strip():
            raise ValidationError("Publisher name cannot be empty.")
        return v.strip()

    @field_validator("app_identifier")
    @classmethod
    def validate_identifier(cls, v: str, info) -> str:
        if not v or not isinstance(v, str) or not v.strip():
            raise ValidationError("Application identifier cannot be empty.")
        identifier = v.strip()
        platform_str = info.data.get("platform", "").upper()
        if platform_str == MobilePlatform.ANDROID.value:
            if not ANDROID_PACKAGE_REGEX.match(identifier):
                raise ValidationError(
                    f"Invalid Android package name format '{identifier}'. Must follow standard convention (e.g. 'com.example.app')."
                )
        elif platform_str == MobilePlatform.IOS.value:
            if not IOS_IDENTIFIER_REGEX.match(identifier):
                raise ValidationError(
                    f"Invalid iOS application identifier format '{identifier}'. Must be a bundle identifier (e.g. 'com.example.app') or App Store ID (e.g. 'id123456789')."
                )
        return identifier

    @field_validator("store_url")
    @classmethod
    def validate_store_url(cls, v: str, info) -> str:
        if not v or not isinstance(v, str):
            raise ValidationError("Store listing URL is required.")
        parsed = urlparse(v.strip())
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValidationError("Store listing URL must be a valid HTTP/HTTPS URL.")
        host = parsed.netloc.lower()
        if ":" in host:
            host = host.split(":")[0]

        platform_str = info.data.get("platform", "").upper()
        if platform_str == MobilePlatform.ANDROID.value:
            if not (host == "play.google.com" or host.endswith(".play.google.com") or host == "market.android.com"):
                raise ValidationError(
                    f"Android store listing URL must be hosted on Google Play ('play.google.com'), received '{host}'."
                )
        elif platform_str == MobilePlatform.IOS.value:
            if not (host == "apps.apple.com" or host.endswith(".apps.apple.com") or host == "itunes.apple.com"):
                raise ValidationError(
                    f"iOS store listing URL must be hosted on Apple App Store ('apps.apple.com'), received '{host}'."
                )
        return v.strip()


class MobileAppUpdate(BaseModel):
    """Payload to update an official mobile application."""

    app_name: Optional[str] = Field(None, min_length=1, max_length=255)
    publisher_name: Optional[str] = Field(None, min_length=1, max_length=255)
    store_url: Optional[str] = Field(None, min_length=5, max_length=512)
    evidence: Optional[str] = Field(None, max_length=1024)
    verification_status: Optional[AssetVerificationStatus] = None

    @field_validator("store_url")
    @classmethod
    def validate_update_store_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        parsed = urlparse(v.strip())
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValidationError("Store listing URL must be a valid HTTP/HTTPS URL.")
        return v.strip()


class MobileAppResponse(BaseModel):
    """Response schema for official brand mobile applications."""

    id: uuid.UUID
    brand_id: uuid.UUID
    app_name: str
    platform: str
    app_identifier: str
    publisher_name: str
    store_url: str
    verification_status: AssetVerificationStatus
    evidence: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
