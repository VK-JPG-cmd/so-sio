from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import AlertStatus, CampaignStatus, EntityType, RelationshipStatus, RelationshipType, RiskSeverity


class ThreatEntityResponse(BaseModel):
    """Schema for a canonical threat entity."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entity_type: EntityType
    canonical_value: str
    first_seen_at: datetime
    last_seen_at: datetime
    created_at: datetime


class EntityRelationshipResponse(BaseModel):
    """Schema for an evidence-backed relationship between two threat entities."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_entity_id: uuid.UUID
    target_entity_id: uuid.UUID
    relationship_type: RelationshipType
    relationship_status: RelationshipStatus
    confidence: Optional[float] = None
    evidence_details: Optional[Dict[str, Any]] = None
    created_at: datetime


class CampaignMembershipResponse(BaseModel):
    """Schema for entity membership in a campaign."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entity_id: uuid.UUID
    relationship_reason: str
    created_at: datetime
    entity: Optional[ThreatEntityResponse] = None


class CampaignResponse(BaseModel):
    """Schema for a correlated threat campaign."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brand_id: uuid.UUID
    title: str
    status: CampaignStatus
    risk_score: float
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    memberships: List[CampaignMembershipResponse] = Field(default_factory=list)


class AlertResponse(BaseModel):
    """Schema for an actionable brand threat alert."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brand_id: uuid.UUID
    campaign_id: Optional[uuid.UUID] = None
    severity: RiskSeverity
    status: AlertStatus
    title: str
    description: str
    dedup_fingerprint: str
    created_at: datetime
    updated_at: datetime


class GraphNode(BaseModel):
    """Visual graph node representation."""

    id: str
    label: str
    type: str  # "ENTITY" | "CAMPAIGN"
    entity_type: Optional[str] = None
    risk_score: Optional[float] = None
    status: Optional[str] = None
    first_seen_at: Optional[str] = None


class GraphEdge(BaseModel):
    """Visual graph connection edge."""

    source: str
    target: str
    relationship_type: str
    status: Optional[str] = None
    confidence: Optional[float] = None
    reason: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class BrandGraphResponse(BaseModel):
    """Complete graph response for brand threat correlation visualization."""

    brand_id: str
    disclaimer: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class CorrelationRunResponse(BaseModel):
    """Summary of a brand correlation pipeline execution."""

    entities_ingested: int
    relationships_created: int
    campaigns_created: int
    alerts_created: int
    message: str

