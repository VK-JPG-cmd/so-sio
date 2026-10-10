import base64
from datetime import datetime
import re
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.enums import AssetType, BrandVerificationStatus


from typing import List
from app.schemas.review import ReviewPublicResponse


class PublicBrandResponse(BaseModel):
    """Publicly discoverable brand profile containing only verified non-sensitive metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    display_name: str
    official_domain: str
    verification_status: BrandVerificationStatus
    created_at: datetime


class PublicBrandDetailResponse(PublicBrandResponse):
    """Public brand profile with approved published customer reviews."""

    published_reviews: List[ReviewPublicResponse] = []


class BrandAssetCreate(BaseModel):
    """Payload to register an official brand asset."""

    asset_type: AssetType
    filename: str = Field(
        ...,
        min_length=3,
        max_length=128,
        description="Filename with extension (e.g. logo.png)",
    )
    content_base64: str = Field(
        ...,
        min_length=10,
        description="Base64 encoded binary content of the asset",
    )

    @field_validator("filename")
    @classmethod
    def sanitize_filename(cls, v: str) -> str:
        import os
        # Strip path traversal by extracting basename
        base = os.path.basename(v.replace("\\", "/"))
        cleaned = re.sub(r"[^a-zA-Z0-9_.-]", "", base.strip())
        cleaned = re.sub(r"^\.+", "", cleaned)
        if not cleaned or "." not in cleaned:
            raise ValueError("Invalid or unsafe filename. Must be a valid filename with extension.")
        return cleaned

    @field_validator("content_base64")
    @classmethod
    def validate_base64(cls, v: str) -> str:
        try:
            base64.b64decode(v, validate=True)
        except Exception:
            raise ValueError("Content must be valid Base64 encoded data.")
        return v


class BrandAssetResponse(BaseModel):
    """Metadata response for a securely stored brand asset."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brand_id: uuid.UUID
    asset_type: AssetType
    storage_key: str
    content_hash: str
    created_at: datetime
