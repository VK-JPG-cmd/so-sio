"""
Mobile Application Store Listing Discovery Connector (Extension Point).
Documented extension point for authorized app store metadata feeds (e.g. Google Play Developer API).
Marked as NOT_CONFIGURED when live enterprise developer credentials are not supplied.
"""

from typing import Optional
from app.services.discovery.connector import (
    ConnectorFetchResult,
    ThreatSourceConnector,
)


class MobileAppStoreDiscoveryConnector(ThreatSourceConnector):
    """
    Extension point connector for app store metadata discovery.
    Requires developer access credentials (e.g. GOOGLE_PLAY_API_SERVICE_ACCOUNT_JSON).
    """

    def __init__(self, service_account_json: Optional[str] = None) -> None:
        self._service_account_json = service_account_json

    @property
    def source_id(self) -> str:
        return "mobile_store_discovery"

    @property
    def source_name(self) -> str:
        return "Mobile App Store Discovery (Extension)"

    def is_configured(self) -> bool:
        """Reports False when store credentials are not provisioned."""
        return bool(self._service_account_json)

    async def fetch_observations(
        self,
        checkpoint: Optional[str] = None,
        limit: int = 50,
    ) -> ConnectorFetchResult:
        """
        Extension point: When store credentials are missing, reports NOT_CONFIGURED
        instead of faking listings or executing live unauthenticated scraping.
        """
        if not self.is_configured():
            return ConnectorFetchResult(
                success=False,
                source_id=self.source_id,
                error_message="Mobile App Store Discovery is NOT_CONFIGURED (requires partner store credentials).",
            )

        return ConnectorFetchResult(
            success=True,
            source_id=self.source_id,
            records=[],
            items_fetched=0,
            items_valid=0,
            items_rejected=0,
        )
