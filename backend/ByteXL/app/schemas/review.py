from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import ReviewStatus


class ReviewCreate(BaseModel):
    """Payload to submit a customer brand review."""

    rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="Rating from 1 to 5 stars",
    )
    body: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Detailed review body text",
    )


class ReviewUpdate(BaseModel):
    """Payload to update an existing customer review or moderate review status."""

    rating: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="Updated rating from 1 to 5 stars",
    )
    body: Optional[str] = Field(
        default=None,
        min_length=10,
        max_length=5000,
        description="Updated review body text",
    )
    status: Optional[ReviewStatus] = Field(
        default=None,
        description="Review moderation status (only modifiable by administrators)",
    )


class ReviewResponse(BaseModel):
    """Detailed review response schema including moderation status and ownership metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brand_id: uuid.UUID
    customer_id: uuid.UUID
    rating: int
    body: str
    status: ReviewStatus
    created_at: datetime
    updated_at: datetime


class ReviewPublicResponse(BaseModel):
    """Public review item visible on brand profile without exposing private customer identifiers."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brand_id: uuid.UUID
    rating: int
    body: str
    status: ReviewStatus
    created_at: datetime
