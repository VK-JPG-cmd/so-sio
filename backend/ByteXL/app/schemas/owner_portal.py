from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import AlertStatus, ReviewStatus, RiskSeverity
from app.schemas.correlation import AlertResponse


class RiskTrendPointResponse(BaseModel):
    """Aggregated risk score trend data point for dashboard visualization."""

    date: str
    assessment_count: int
    average_risk_score: float
    max_risk_score: float


class BrandDashboardSummaryResponse(BaseModel):
    """Comprehensive brand owner dashboard summary backed by live database aggregations."""

    brand_id: uuid.UUID
    total_threat_reports: int
    threats_by_severity: Dict[str, int]
    threats_by_status: Dict[str, int]
    recent_alerts: List[AlertResponse]
    open_investigations: int
    campaign_count: int
    recent_risk_score_trends: List[RiskTrendPointResponse]


class AlertStatusUpdate(BaseModel):
    """Payload to update an alert's incident resolution status."""

    status: AlertStatus
    notes: Optional[str] = Field(default=None, max_length=1000, description="Optional incident notes")


class BrandMetadataUpdate(BaseModel):
    """
    Payload for brand owners to update approved brand metadata.
    Direct modification of verification status is strictly rejected.
    """

    display_name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=255,
        description="Public brand display name",
    )


class ReviewOwnerResponseCreate(BaseModel):
    """Payload to publish an official brand owner response to a customer review."""

    response_text: str = Field(
        ...,
        min_length=5,
        max_length=5000,
        description="Official brand response message",
    )


class ReviewOwnerResponseDTO(BaseModel):
    """Official brand owner response data transfer object."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    review_id: uuid.UUID
    brand_id: uuid.UUID
    responder_user_id: uuid.UUID
    response_text: str
    created_at: datetime
    updated_at: datetime


class ReviewWithOwnerResponseDTO(BaseModel):
    """Customer review with attached official brand response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brand_id: uuid.UUID
    customer_id: uuid.UUID
    rating: int
    body: str
    status: ReviewStatus
    created_at: datetime
    updated_at: datetime
    owner_response: Optional[ReviewOwnerResponseDTO] = None


class AuditLogResponse(BaseModel):
    """Structured audit trail record for sensitive actions."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_user_id: uuid.UUID
    brand_id: Optional[uuid.UUID] = None
    action: str
    entity_type: str
    entity_id: str
    details: Dict[str, Any]
    created_at: datetime
