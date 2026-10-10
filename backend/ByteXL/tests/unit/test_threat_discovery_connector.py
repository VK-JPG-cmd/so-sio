"""
Unit tests for Threat Discovery Connector Architecture and URLhaus Connector:
- Indicator normalization across URLs and domains
- SSRF prevention (rejecting loopback, private, and link-local destinations)
- Provider response parsing and field extraction
- Provider authentication failure handling (HTTP 401/403)
- Rate-limit backoff and error envelope handling (HTTP 429)
- Provider timeout and transport error handling
- Malformed response resilience
- Incremental checkpoint filtering
- Disabled/unconfigured connector handling
- Social and Mobile extension point behavior
"""

import httpx
import pytest
from app.models.enums import EntityType
from app.services.discovery.connectors.mobile_mock import MobileAppStoreDiscoveryConnector
from app.services.discovery.connectors.social_mock import SocialMediaDiscoveryConnector
from app.services.discovery.connectors.urlhaus import URLhausConnector


def test_urlhaus_indicator_normalization_and_syntax() -> None:
    """Verify that URL indicators are normalized properly."""
    connector = URLhausConnector(base_url="https://urlhaus-api.abuse.ch/v1")

    # 1. Valid HTTP URL
    raw_payload = {
        "id": 1001,
        "dateadded": "2026-10-10 12:00:00 UTC",
        "threat": "malware_download",
        "tags": ["elf", "mirai"],
        "url_status": "online",
    }
    rec = connector._normalize_indicator("HTTP://Evil-Domain.com/Path/Payload.bin?id=1#frag", raw_payload)
    assert rec is not None
    assert rec.source_id == "urlhaus"
    assert rec.source_record_id == "1001"
    assert rec.indicator_type == EntityType.URL
    assert rec.canonical_value == "http://evil-domain.com/path/payload.bin?id=1"
    assert "mirai" in rec.tags
    assert rec.source_first_seen_at is not None

    # 2. Invalid schemes rejected
    assert connector._normalize_indicator("ftp://evil.com/file", {}) is None
    assert connector._normalize_indicator("javascript:alert(1)", {}) is None
    assert connector._normalize_indicator("file:///etc/passwd", {}) is None


def test_urlhaus_ssrf_protection_guards() -> None:
    """
    CRITICAL SECURITY INVARIANT:
    Discovered indicators pointing to private, loopback, or metadata addresses
    must be discarded immediately to prevent SSRF and internal scanning.
    """
    connector = URLhausConnector(base_url="https://urlhaus-api.abuse.ch/v1")

    # Loopback targets
    assert connector._normalize_indicator("http://127.0.0.1:8080/c2", {}) is None
    assert connector._normalize_indicator("http://localhost/admin", {}) is None
    assert connector._normalize_indicator("http://[::1]/status", {}) is None

    # Private network ranges
    assert connector._normalize_indicator("http://10.0.0.1/malware", {}) is None
    assert connector._normalize_indicator("http://192.168.1.100/dropper", {}) is None
    assert connector._normalize_indicator("http://172.16.0.5/c2", {}) is None

    # Cloud metadata service (169.254.169.254 / metadata.google.internal)
    assert connector._normalize_indicator("http://169.254.169.254/latest/meta-data/", {}) is None
    assert connector._normalize_indicator("http://metadata.google.internal/computeMetadata", {}) is None


@pytest.mark.asyncio
async def test_urlhaus_successful_response_parsing_and_checkpoint() -> None:
    """Verify parsing valid URLhaus JSON response and calculating new checkpoint."""
    mock_response_data = {
        "query_status": "ok",
        "urls": [
            {
                "id": "501",
                "url": "http://phish-bank-alpha.com/login",
                "dateadded": "2026-10-10 10:00:00 UTC",
                "threat": "credential_stealer",
                "tags": ["phish"],
            },
            {
                "id": "502",
                "url": "https://malware-drop-beta.net/payload.exe",
                "dateadded": "2026-10-10 11:00:00 UTC",
                "threat": "malware_download",
                "tags": ["exe", "stealer"],
            },
        ],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=mock_response_data)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        connector = URLhausConnector(base_url="https://urlhaus-api.abuse.ch/v1", client=client)
        result = await connector.fetch_observations(checkpoint="500", limit=10)

        assert result.success is True
        assert result.items_fetched == 2
        assert result.items_valid == 2
        assert len(result.records) == 2
        assert result.new_checkpoint == "502"
        assert result.records[0].canonical_value == "http://phish-bank-alpha.com/login"
        assert result.records[1].canonical_value == "https://malware-drop-beta.net/payload.exe"


@pytest.mark.asyncio
async def test_urlhaus_incremental_checkpoint_filtering() -> None:
    """Verify that records below or equal to the checkpoint are skipped."""
    mock_response_data = {
        "query_status": "ok",
        "urls": [
            {"id": "499", "url": "http://old-threat.com/a"},
            {"id": "500", "url": "http://seen-threat.com/b"},
            {"id": "505", "url": "http://new-threat.com/c"},
        ],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=mock_response_data)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        connector = URLhausConnector(base_url="https://urlhaus-api.abuse.ch/v1", client=client)
        # Checkpoint is 500: only 505 should be returned as new
        result = await connector.fetch_observations(checkpoint="500", limit=10)

        assert result.success is True
        assert len(result.records) == 1
        assert result.records[0].source_record_id == "505"
        assert result.new_checkpoint == "505"


@pytest.mark.asyncio
async def test_urlhaus_authentication_failure_handling() -> None:
    """Verify that HTTP 401/403 responses return clear structured error without retries."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "Invalid Auth-Key"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        connector = URLhausConnector(base_url="https://urlhaus-api.abuse.ch/v1", client=client)
        result = await connector.fetch_observations()

        assert result.success is False
        assert result.status_code == 401
        assert "Authentication" in result.error_message


@pytest.mark.asyncio
async def test_urlhaus_rate_limit_handling() -> None:
    """Verify that HTTP 429 returns rate_limited=True in result envelope."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": "Too Many Requests"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        connector = URLhausConnector(
            base_url="https://urlhaus-api.abuse.ch/v1", max_retries=0, client=client
        )
        result = await connector.fetch_observations()

        assert result.success is False
        assert result.status_code == 429
        assert result.rate_limited is True
        assert "Rate limit" in result.error_message


@pytest.mark.asyncio
async def test_urlhaus_timeout_handling() -> None:
    """Verify timeout exception is caught and reported gracefully."""
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Connection timed out")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        connector = URLhausConnector(
            base_url="https://urlhaus-api.abuse.ch/v1", max_retries=0, client=client
        )
        result = await connector.fetch_observations()

        assert result.success is False
        assert "timed out" in result.error_message


@pytest.mark.asyncio
async def test_urlhaus_malformed_response_handling() -> None:
    """Verify handling when provider returns invalid JSON or unexpected status."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>502 Bad Gateway</html>")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        connector = URLhausConnector(base_url="https://urlhaus-api.abuse.ch/v1", client=client)
        result = await connector.fetch_observations()

        assert result.success is False
        assert "error" in result.error_message.lower()


def test_social_and_mobile_extension_points_report_not_configured() -> None:
    """
    Verify extension points for social media and mobile app store feeds
    cleanly report NOT_CONFIGURED when API keys are absent.
    """
    social = SocialMediaDiscoveryConnector(api_key=None)
    assert social.is_configured() is False

    mobile = MobileAppStoreDiscoveryConnector(service_account_json=None)
    assert mobile.is_configured() is False
