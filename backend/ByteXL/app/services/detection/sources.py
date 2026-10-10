"""
Discovery sources and adapter architecture for threat intake.
BrandShield AI does not claim to scan the entire internet automatically.
All monitored items originate from explicit, authorized discovery channels.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class DiscoverySourceType(str, Enum):
    """Explicitly supported intake channels for threat indicators."""

    CUSTOMER_REPORT = "CUSTOMER_REPORT"
    AUTHORIZED_SEARCH_API = "AUTHORIZED_SEARCH_API"
    IMPORTED_DATASET = "IMPORTED_DATASET"
    THREAT_INTEL_FEED = "THREAT_INTEL_FEED"
    AUTHORIZED_PLATFORM_API = "AUTHORIZED_PLATFORM_API"


class DiscoveredIndicator(BaseModel):
    """Standardized representation of a threat candidate ingested from an authorized channel."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    source_type: DiscoverySourceType
    source_identifier: str = Field(..., description="Unique ID or URL of the provider / source")
    indicator_type: str = Field(..., description="DOMAIN, URL, SOCIAL_PROFILE, SCAM_TEXT, or APK")
    indicator_value: str
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseSourceAdapter(ABC):
    """Abstract adapter interface allowing new intake feeds to be integrated seamlessly."""

    @property
    @abstractmethod
    def source_type(self) -> DiscoverySourceType:
        """The category of this intake source."""
        pass

    @abstractmethod
    async def ingest_indicator(self, raw_input: Any, **kwargs: Any) -> DiscoveredIndicator:
        """Parse raw intake data into a validated DiscoveredIndicator."""
        pass


class CustomerReportSourceAdapter(BaseSourceAdapter):
    """Ingests candidate threats directly submitted by verified platform customers."""

    @property
    def source_type(self) -> DiscoverySourceType:
        return DiscoverySourceType.CUSTOMER_REPORT

    async def ingest_indicator(self, raw_input: Any, **kwargs: Any) -> DiscoveredIndicator:
        report_id = kwargs.get("report_id", "direct-submission")
        reporter_id = kwargs.get("reporter_id", "anonymous")
        indicator_type = kwargs.get("indicator_type", "UNKNOWN")

        return DiscoveredIndicator(
            source_type=self.source_type,
            source_identifier=f"report:{report_id}",
            indicator_type=indicator_type,
            indicator_value=str(raw_input).strip(),
            metadata={"reporter_id": str(reporter_id), "source_notes": "Customer submitted via API"},
        )


class ThreatIntelFeedAdapter(BaseSourceAdapter):
    """Ingests IOCs (Indicators of Compromise) from configured threat intelligence feeds."""

    @property
    def source_type(self) -> DiscoverySourceType:
        return DiscoverySourceType.THREAT_INTEL_FEED

    async def ingest_indicator(self, raw_input: Any, **kwargs: Any) -> DiscoveredIndicator:
        feed_name = kwargs.get("feed_name", "configured-ioc-feed")
        indicator_type = kwargs.get("indicator_type", "DOMAIN")

        return DiscoveredIndicator(
            source_type=self.source_type,
            source_identifier=f"feed:{feed_name}",
            indicator_type=indicator_type,
            indicator_value=str(raw_input).strip(),
            metadata={"feed_name": feed_name, "confidence": kwargs.get("confidence", "HIGH")},
        )


class AuthorizedSearchApiAdapter(BaseSourceAdapter):
    """Ingests URLs/domains discovered through authorized search engines and monitoring APIs."""

    @property
    def source_type(self) -> DiscoverySourceType:
        return DiscoverySourceType.AUTHORIZED_SEARCH_API

    async def ingest_indicator(self, raw_input: Any, **kwargs: Any) -> DiscoveredIndicator:
        api_name = kwargs.get("api_name", "authorized-search")
        query = kwargs.get("query", "")

        return DiscoveredIndicator(
            source_type=self.source_type,
            source_identifier=f"api:{api_name}",
            indicator_type="URL",
            indicator_value=str(raw_input).strip(),
            metadata={"search_api": api_name, "search_query": query},
        )


class ImportedDatasetAdapter(BaseSourceAdapter):
    """Ingests offline batch datasets (e.g. security audits, incident response dumps)."""

    @property
    def source_type(self) -> DiscoverySourceType:
        return DiscoverySourceType.IMPORTED_DATASET

    async def ingest_indicator(self, raw_input: Any, **kwargs: Any) -> DiscoveredIndicator:
        dataset_name = kwargs.get("dataset_name", "incident-import")

        return DiscoveredIndicator(
            source_type=self.source_type,
            source_identifier=f"dataset:{dataset_name}",
            indicator_type=kwargs.get("indicator_type", "DOMAIN"),
            indicator_value=str(raw_input).strip(),
            metadata={"dataset": dataset_name, "batch_id": kwargs.get("batch_id")},
        )


class AuthorizedPlatformApiAdapter(BaseSourceAdapter):
    """Ingests profiles/posts from authorized platform partner APIs (e.g. X, Instagram, LinkedIn)."""

    @property
    def source_type(self) -> DiscoverySourceType:
        return DiscoverySourceType.AUTHORIZED_PLATFORM_API

    async def ingest_indicator(self, raw_input: Any, **kwargs: Any) -> DiscoveredIndicator:
        platform = kwargs.get("platform", "generic-platform")

        return DiscoveredIndicator(
            source_type=self.source_type,
            source_identifier=f"platform:{platform}",
            indicator_type="SOCIAL_PROFILE",
            indicator_value=str(raw_input).strip(),
            metadata={"platform": platform, "account_id": kwargs.get("account_id")},
        )
