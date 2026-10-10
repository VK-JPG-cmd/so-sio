"""
Schemas for Threat Discovery and Continuous Monitoring Telemetry.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SourceHealthSummary(BaseModel):
    """Health and checkpoint status for an individual threat connector."""

    source_id: str
    source_name: str
    is_configured: bool
    status: str  # IDLE, POLLING, ERROR, NOT_CONFIGURED, DISABLED
    last_poll_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_error_at: Optional[datetime] = None
    last_error_message: Optional[str] = None
    indicators_fetched_total: int = 0
    indicators_accepted_total: int = 0
    indicators_rejected_total: int = 0
    poll_count: int = 0
    checkpoint_value: Optional[str] = None


class DiscoveryHealthResponse(BaseModel):
    """Authoritative administrative health status of threat discovery infrastructure."""

    worker_running: bool
    worker_enabled: bool
    overall_status: str  # HEALTHY, DEGRADED, NOT_CONFIGURED, DISABLED
    poll_interval_seconds: int
    batch_size: int
    configured_sources: int
    active_sources: int
    sources: List[SourceHealthSummary] = Field(default_factory=list)


class DiscoveryStatsResponse(BaseModel):
    """Aggregated observation metrics across discovery sources."""

    total_indicators: int
    status_counts: Dict[str, int]
    sources_count: int


class DiscoveryRunNowResponse(BaseModel):
    """Execution acknowledgement and result for on-demand discovery cycle."""

    status: str
    duration_seconds: Optional[float] = None
    connectors_processed: int = 0
    total_fetched: int = 0
    total_valid: int = 0
    total_rejected: int = 0
    details: List[Dict[str, Any]] = Field(default_factory=list)


class DiscoveredIndicatorResponse(BaseModel):
    """Detailed external threat observation record."""

    id: Any
    source_id: str
    source_record_id: Optional[str] = None
    indicator_type: str
    raw_indicator: str
    canonical_value: str
    source_first_seen_at: Optional[datetime] = None
    source_last_seen_at: Optional[datetime] = None
    ingested_at: datetime
    last_observed_at: datetime
    processed_at: Optional[datetime] = None
    processing_status: str
    brand_id: Optional[Any] = None
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    threat_entity_id: Optional[Any] = None
    campaign_id: Optional[Any] = None
    alert_id: Optional[Any] = None
    evidence_payload: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}

