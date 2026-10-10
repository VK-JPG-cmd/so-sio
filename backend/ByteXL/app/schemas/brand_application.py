from datetime import datetime
from typing import Literal, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.core.domain import normalize_domain
from app.models.enums import ApplicationStatus


class BrandApplicationCreate(BaseModel):
    """Payload to submit a new official brand application."""

    business_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Official registered business entity or organization name",
        examples=["Acme Corporation"],
    )
    official_domain: str = Field(
        ...,
        min_length=4,
        max_length=255,
        description="Official primary domain name belonging to the organization",
        examples=["acme.com"],
    )

    @field_validator("business_name")
    @classmethod
    def validate_business(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Business name cannot be empty.")
        return cleaned

    @field_validator("official_domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        return normalize_domain(v)


class BrandApplicationResponse(BaseModel):
    """Complete application response representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_user_id: uuid.UUID
    business_name: str
    official_domain: str
    application_status: ApplicationStatus
    submitted_at: datetime
    reviewed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class DomainChallengeResponse(BaseModel):
    """Challenge instructions returned to owner for DNS verification."""

    application_id: uuid.UUID
    domain: str
    record_type: str = "TXT"
    record_host: str
    challenge_token: str
    expected_record_value: str
    expires_at: datetime


class DomainVerifyRequest(BaseModel):
    """Payload to trigger DNS verification against live TXT records."""

    token: str = Field(
        ...,
        min_length=16,
        description="The secret challenge token issued during challenge generation",
    )


class DomainVerifyResponse(BaseModel):
    """Outcome of domain DNS ownership verification check."""

    application_id: uuid.UUID
    official_domain: str
    verified: bool
    application_status: ApplicationStatus
    message: str
    verified_at: Optional[datetime] = None


class AdminReviewRequest(BaseModel):
    """Payload for manual administrative review of an application."""

    decision: Literal["APPROVE", "REJECT"]
    notes: Optional[str] = Field(default=None, description="Optional reviewer remarks")


class AdminReviewResponse(BaseModel):
    """Result of administrative review action."""

    application_id: uuid.UUID
    application_status: ApplicationStatus
    reviewed_at: datetime
    brand_id: Optional[uuid.UUID] = None
    message: str
