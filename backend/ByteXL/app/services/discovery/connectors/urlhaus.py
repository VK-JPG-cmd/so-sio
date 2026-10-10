"""
abuse.ch URLhaus Threat Intelligence Connector.
Queries authoritative malicious URL and payload feed from abuse.ch URLhaus.
Supports incremental checkpointing, exponential backoff, rate limit handling,
and SSRF-safe indicator normalization.
"""

import asyncio
from datetime import datetime, timezone
import ipaddress
import random
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import httpx
from pydantic import BaseModel
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.enums import EntityType
from app.services.correlation.normalization import normalize_threat_entity
from app.services.discovery.connector import (
    ConnectorFetchResult,
    DiscoveredIndicatorRecord,
    ThreatSourceConnector,
)

logger = get_logger("app.services.discovery.connectors.urlhaus")


class URLhausConnector(ThreatSourceConnector):
    """
    Authorized threat intelligence connector for abuse.ch URLhaus feed.
    Retrieves recent malware and phishing distribution URLs.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        auth_key: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        settings = get_settings()
        self._base_url = (base_url or settings.URLHAUS_API_URL).rstrip("/")
        self._auth_key = auth_key or settings.URLHAUS_AUTH_KEY
        self._timeout = timeout if timeout is not None else settings.URLHAUS_TIMEOUT_SECONDS
        self._max_retries = max_retries if max_retries is not None else settings.URLHAUS_MAX_RETRIES
        self._custom_client = client

    @property
    def source_id(self) -> str:
        return "urlhaus"

    @property
    def source_name(self) -> str:
        return "abuse.ch URLhaus"

    def is_configured(self) -> bool:
        """URLhaus is active when enabled in settings and base_url is present."""
        settings = get_settings()
        return bool(settings.URLHAUS_ENABLED and self._base_url)

    async def fetch_observations(
        self,
        checkpoint: Optional[str] = None,
        limit: int = 50,
    ) -> ConnectorFetchResult:
        """
        Poll URLhaus recent URLs feed.
        Supports bounded limits, backoff on HTTP 429/5xx, and safe parsing.
        """
        if not self.is_configured():
            return ConnectorFetchResult(
                success=False,
                source_id=self.source_id,
                error_message="URLhaus connector is disabled or NOT_CONFIGURED.",
            )

        endpoint = f"{self._base_url}/urls/recent/"
        headers = {
            "User-Agent": "BrandShield-AI-Security-Monitor/1.0",
            "Accept": "application/json",
        }
        if self._auth_key:
            headers["Auth-Key"] = str(self._auth_key)

        # Build payload
        payload: Dict[str, Any] = {"limit": min(limit, 500)}

        attempt = 0
        last_error = None
        status_code = None

        while attempt <= self._max_retries:
            attempt += 1
            try:
                if self._custom_client:
                    response = await self._custom_client.post(
                        endpoint, json=payload, headers=headers, timeout=self._timeout
                    )
                else:
                    async with httpx.AsyncClient(verify=True, timeout=self._timeout) as client:
                        response = await client.post(endpoint, json=payload, headers=headers)

                status_code = response.status_code

                if status_code == 429:
                    logger.warning("URLhaus rate limit hit (HTTP 429). Backing off.")
                    if attempt <= self._max_retries:
                        backoff = (2 ** attempt) + random.uniform(0.1, 0.5)
                        await asyncio.sleep(backoff)
                        continue
                    return ConnectorFetchResult(
                        success=False,
                        source_id=self.source_id,
                        status_code=429,
                        rate_limited=True,
                        error_message="Rate limit exceeded from URLhaus API (HTTP 429).",
                    )

                if status_code in (401, 403):
                    logger.warning(
                        f"URLhaus API key required or rejected (HTTP {status_code}). "
                        "Set URLHAUS_AUTH_KEY in .env to enable abuse.ch feed ingestion."
                    )
                    return ConnectorFetchResult(
                        success=False,
                        source_id=self.source_id,
                        status_code=status_code,
                        error_message=(
                            f"Authentication rejected by URLhaus (HTTP {status_code}). "
                            "abuse.ch requires an Auth-Key (set URLHAUS_AUTH_KEY in .env)."
                        ),
                    )

                if status_code >= 500:
                    logger.warning(f"URLhaus server error (HTTP {status_code}). Attempt {attempt}.")
                    if attempt <= self._max_retries:
                        backoff = (2 ** attempt) + random.uniform(0.1, 0.5)
                        await asyncio.sleep(backoff)
                        continue
                    return ConnectorFetchResult(
                        success=False,
                        source_id=self.source_id,
                        status_code=status_code,
                        error_message=f"URLhaus server error (HTTP {status_code}) after retries.",
                    )

                response.raise_for_status()
                data = response.json()
                return self._parse_urlhaus_response(data, checkpoint)

            except httpx.TimeoutException as exc:
                last_error = f"URLhaus request timed out: {str(exc)}"
                logger.warning(f"URLhaus timeout on attempt {attempt}: {exc}")
                if attempt <= self._max_retries:
                    await asyncio.sleep((2 ** attempt) * 0.5)
                    continue
            except httpx.RequestError as exc:
                last_error = f"URLhaus transport error: {str(exc)}"
                logger.warning(f"URLhaus request error on attempt {attempt}: {exc}")
                if attempt <= self._max_retries:
                    await asyncio.sleep((2 ** attempt) * 0.5)
                    continue
            except Exception as exc:
                last_error = f"Unexpected URLhaus response processing error: {str(exc)}"
                logger.error(f"Unexpected error querying URLhaus: {exc}", exc_info=True)
                break

        return ConnectorFetchResult(
            success=False,
            source_id=self.source_id,
            status_code=status_code,
            error_message=last_error or "URLhaus connection failed.",
        )

    def _parse_urlhaus_response(
        self,
        data: Dict[str, Any],
        checkpoint: Optional[str],
    ) -> ConnectorFetchResult:
        """Safely parse and filter raw URLhaus JSON payload."""
        if not isinstance(data, dict):
            return ConnectorFetchResult(
                success=False,
                source_id=self.source_id,
                error_message="Malformed response: expected JSON object.",
            )

        query_status = data.get("query_status")
        if query_status != "ok" and "urls" not in data:
            return ConnectorFetchResult(
                success=False,
                source_id=self.source_id,
                error_message=f"URLhaus reported status: {query_status}",
            )

        raw_urls = data.get("urls") or []
        if not isinstance(raw_urls, list):
            raw_urls = []

        records: List[DiscoveredIndicatorRecord] = []
        max_id: Optional[int] = None
        checkpoint_id = None
        if checkpoint:
            try:
                checkpoint_id = int(checkpoint)
            except ValueError:
                checkpoint_id = None

        items_rejected = 0

        for item in raw_urls:
            if not isinstance(item, dict):
                items_rejected += 1
                continue

            record_id_raw = item.get("id")
            url_raw = item.get("url")

            if not url_raw or not isinstance(url_raw, str):
                items_rejected += 1
                continue

            # Checkpoint filtering: skip records already seen if numeric checkpoint exists
            try:
                record_id_int = int(record_id_raw) if record_id_raw is not None else None
            except (ValueError, TypeError):
                record_id_int = None

            if checkpoint_id is not None and record_id_int is not None:
                if record_id_int <= checkpoint_id:
                    continue  # Already processed in previous polling cycle

            if record_id_int is not None:
                if max_id is None or record_id_int > max_id:
                    max_id = record_id_int

            # Validate and normalize
            parsed_record = self._normalize_indicator(url_raw, item)
            if parsed_record:
                records.append(parsed_record)
            else:
                items_rejected += 1

        new_checkpoint_str = str(max_id) if max_id is not None else checkpoint

        return ConnectorFetchResult(
            success=True,
            source_id=self.source_id,
            records=records,
            new_checkpoint=new_checkpoint_str,
            items_fetched=len(raw_urls),
            items_valid=len(records),
            items_rejected=items_rejected,
        )

    def _normalize_indicator(
        self,
        raw_url: str,
        raw_payload: Dict[str, Any],
    ) -> Optional[DiscoveredIndicatorRecord]:
        """
        Validate URL syntax, protect against SSRF targets, and normalize.
        Rejects loopback, private, or metadata IPs.
        """
        raw_url = raw_url.strip()
        if len(raw_url) < 4 or len(raw_url) > 2048:
            return None

        # Syntax check via urlparse
        try:
            parsed = urlparse(raw_url)
            if parsed.scheme.lower() not in ("http", "https"):
                return None
            hostname = parsed.hostname
            if not hostname:
                return None
        except Exception:
            return None

        # SSRF Guard: Reject loopback, link-local, private, and reserved IPs
        if self._is_forbidden_destination(hostname):
            logger.warning(f"Rejected unsafe/SSRF indicator target: {hostname}")
            return None

        # Canonicalize
        canonical = normalize_threat_entity(raw_url, EntityType.URL)
        if not canonical:
            return None

        # Parse dateadded
        first_seen = None
        dateadded_raw = raw_payload.get("dateadded")
        if dateadded_raw and isinstance(dateadded_raw, str):
            for fmt in ("%Y-%m-%d %H:%M:%S UTC", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
                try:
                    first_seen = datetime.strptime(dateadded_raw.strip(), fmt).replace(
                        tzinfo=timezone.utc
                    )
                    break
                except ValueError:
                    pass

        tags_raw = raw_payload.get("tags") or []
        tags = [str(t).strip().lower() for t in tags_raw if str(t).strip()]

        rec_id = str(raw_payload.get("id")) if raw_payload.get("id") is not None else None

        return DiscoveredIndicatorRecord(
            source_id=self.source_id,
            source_record_id=rec_id,
            indicator_type=EntityType.URL,
            raw_indicator=raw_url,
            canonical_value=canonical,
            source_first_seen_at=first_seen,
            source_last_seen_at=datetime.now(timezone.utc),
            tags=tags,
            raw_payload={
                "threat": raw_payload.get("threat"),
                "url_status": raw_payload.get("url_status"),
                "reporter": raw_payload.get("reporter"),
                "urlhaus_reference": raw_payload.get("urlhaus_reference"),
            },
        )

    def _is_forbidden_destination(self, host: str) -> bool:
        """Verify host is not localhost, private network, or cloud metadata IP."""
        host_lower = host.lower()
        if host_lower in ("localhost", "127.0.0.1", "::1", "metadata.google.internal"):
            return True
        try:
            ip = ipaddress.ip_address(host_lower)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return True
        except ValueError:
            pass  # Standard domain name
        return False
