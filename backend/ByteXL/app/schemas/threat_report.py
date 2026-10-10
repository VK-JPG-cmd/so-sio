from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse
import uuid
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.core.domain import normalize_domain
from app.models.enums import TargetType, ThreatReportStatus
from app.schemas.evidence import EvidenceResponse


class ThreatReportCreate(BaseModel):
    """Payload to submit a suspected digital threat, impersonation, or scam report."""

    brand_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Optional ID of the brand being impersonated or targeted",
    )
    target_type: TargetType = Field(
        ...,
        description="Category of the targeted attack surface",
    )
    target_value: str = Field(
        ...,
        min_length=1,
        max_length=2048,
        description="Domain, URL, handle, or identifier of the threat",
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=10000,
        description="Detailed description of the malicious activity, context, and impact",
    )

    @model_validator(mode="after")
    def validate_target_value_by_type(self) -> "ThreatReportCreate":
        raw = self.target_value.strip()
        if not raw:
            raise ValueError("Target value cannot be empty.")

        if self.target_type == TargetType.DOMAIN:
            # Validate and canonicalize domain format
            self.target_value = normalize_domain(raw)

        elif self.target_type == TargetType.URL:
            # Must be a well-formed HTTP/HTTPS URL
            parsed = urlparse(raw)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                raise ValueError("Target URL must begin with http:// or https:// and include a valid host.")
            self.target_value = raw

        else:
            self.target_value = raw

        return self


class ThreatReportStatusUpdate(BaseModel):
    """Payload for investigators/admins to transition threat report status."""

    status: ThreatReportStatus = Field(
        ...,
        description="New lifecycle status of the threat report",
    )


class ThreatReportResponse(BaseModel):
    """Full threat report response schema including investigation status and attached evidence."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reporter_id: uuid.UUID
    brand_id: Optional[uuid.UUID]
    target_type: TargetType
    target_value: str
    description: str
    status: ThreatReportStatus
    created_at: datetime
    updated_at: datetime
    evidences: List[EvidenceResponse] = []
