from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import RiskSeverity


class SignalItemSchema(BaseModel):
    """Schema for individual contributing indicator."""

    category: str
    signal_type: str
    points: float
    description: str
    evidence_context: Dict[str, Any] = Field(default_factory=dict)


class RecommendationSchema(BaseModel):
    """Actionable recommendation step."""

    action: str
    title: str
    description: str


class RiskAssessmentResponse(BaseModel):
    """Public representation of an explainable threat risk assessment."""

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: uuid.UUID
    report_id: Optional[uuid.UUID]
    entity_id: Optional[str]
    model_version: str
    risk_score: float = Field(..., ge=0.0, le=100.0)
    severity: RiskSeverity
    confidence: Optional[float] = None
    explanation_json: Dict[str, Any]
    indicators_json: List[Dict[str, Any]]
    recommendation_json: List[Dict[str, Any]]
    created_at: datetime
