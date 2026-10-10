"""
Threat Source Connector Abstract Architecture.
Provides uniform interfaces for threat intelligence ingestion, normalization,
provenance tracking, and rate-limit handling across diverse intelligence feeds.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.models.enums import EntityType


class DiscoveredIndicatorRecord(BaseModel):
    """Normalized observation record returned by a threat source connector."""

    source_id: str
    source_record_id: Optional[str] = None
    indicator_type: EntityType
    raw_indicator: str
    canonical_value: str
    source_first_seen_at: Optional[datetime] = None
    source_last_seen_at: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    raw_payload: Dict[str, Any] = Field(default_factory=dict)


class ConnectorFetchResult(BaseModel):
    """Result envelope for a connector polling cycle."""

    success: bool
    source_id: str
    records: List[DiscoveredIndicatorRecord] = Field(default_factory=list)
    new_checkpoint: Optional[str] = None
    error_message: Optional[str] = None
    status_code: Optional[int] = None
    rate_limited: bool = False
    items_fetched: int = 0
    items_valid: int = 0
    items_rejected: int = 0


class ThreatSourceConnector(ABC):
    """
    Abstract interface for external threat intelligence and discovery sources.
    Adapters implement fetching, authentication, pagination, rate limit backoff,
    and syntactic validation for specific external threat feeds.
    """

    @property
    @abstractmethod
    def source_id(self) -> str:
        """Unique identifier for this connector (e.g., 'urlhaus')."""
        pass

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Human-readable display name for the source."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Verify whether required settings or API keys are present."""
        pass

    @abstractmethod
    async def fetch_observations(
        self,
        checkpoint: Optional[str] = None,
        limit: int = 50,
    ) -> ConnectorFetchResult:
        """
        Retrieve available threat observations from the source.
        Supports incremental retrieval via checkpoint and bounded batch limit.
        """
        pass
