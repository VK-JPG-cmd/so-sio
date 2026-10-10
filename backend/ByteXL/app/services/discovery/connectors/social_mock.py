"""
Social Media Impersonation Discovery Connector (Extension Point).
Documented extension point for authorized social media API ingestion (e.g. X/Twitter, Instagram).
Marked as NOT_CONFIGURED when live enterprise developer credentials are not supplied.
"""

from typing import Optional
from app.services.discovery.connector import (
    ConnectorFetchResult,
    ThreatSourceConnector,
)


class SocialMediaDiscoveryConnector(ThreatSourceConnector):
    """
    Extension point connector for official social platform monitoring APIs.
    Requires developer access tokens (e.g. TWITTER_BEARER_TOKEN, META_GRAPH_TOKEN).
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key = api_key

    @property
    def source_id(self) -> str:
        return "social_platform_discovery"

    @property
    def source_name(self) -> str:
        return "Social Media Impersonation Discovery (Extension)"

    def is_configured(self) -> bool:
        """Reports False when developer API credentials are not provisioned."""
        return bool(self._api_key)

    async def fetch_observations(
        self,
        checkpoint: Optional[str] = None,
        limit: int = 50,
    ) -> ConnectorFetchResult:
        """
        Extension point: When API keys are missing, reports NOT_CONFIGURED
        instead of pretending to discover live social threats.
        """
        if not self.is_configured():
            return ConnectorFetchResult(
                success=False,
                source_id=self.source_id,
                error_message="Social Media Discovery is NOT_CONFIGURED (requires partner API credentials).",
            )

        return ConnectorFetchResult(
            success=True,
            source_id=self.source_id,
            records=[],
            items_fetched=0,
            items_valid=0,
            items_rejected=0,
        )
