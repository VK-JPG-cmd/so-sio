from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import dns.asyncresolver
import dns.exception
import dns.resolver
from app.core.config import get_settings
from app.core.exceptions import ConfigurationError
from app.core.logging import get_logger

logger = get_logger("app.services.dns")
settings = get_settings()


class BaseDNSResolver(ABC):
    """Abstract DNS resolver interface for TXT record inspection."""

    @abstractmethod
    async def query_txt_records(self, host: str) -> List[str]:
        """Query and return all TXT record string values for the given host."""
        pass


class SystemDNSResolver(BaseDNSResolver):
    """Live DNS resolver using asynchronous dnspython queries."""

    def __init__(self, timeout: float = 5.0) -> None:
        self.resolver = dns.asyncresolver.Resolver()
        self.resolver.timeout = timeout
        self.resolver.lifetime = timeout

    async def query_txt_records(self, host: str) -> List[str]:
        records: List[str] = []
        try:
            answers = await self.resolver.resolve(host, "TXT")
            for rdata in answers:
                # In dnspython, rdata.strings is a tuple of bytes
                text = "".join(s.decode("utf-8", errors="replace") for s in rdata.strings)
                records.append(text)
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
            logger.debug(f"No TXT records found for {host}")
        except dns.resolver.Timeout:
            logger.warning(f"DNS lookup timed out for {host}")
        except dns.exception.DNSException as exc:
            logger.warning(f"DNS error querying {host}: {str(exc)}")
        except Exception as exc:
            logger.error(f"Unexpected error during DNS resolution for {host}: {str(exc)}")

        return records


class MockDNSResolver(BaseDNSResolver):
    """Mock DNS resolver for automated testing and local staging."""

    def __init__(self) -> None:
        if settings.ENVIRONMENT.lower() == "production":
            raise ConfigurationError("MockDNSResolver cannot be initialized in production.")
        self.records: Dict[str, List[str]] = {}

    def set_txt_records(self, host: str, values: List[str]) -> None:
        """Register simulated TXT records for a host."""
        self.records[host.strip().lower()] = values

    def clear(self) -> None:
        """Clear all registered records."""
        self.records.clear()

    async def query_txt_records(self, host: str) -> List[str]:
        normalized_host = host.strip().lower()
        return list(self.records.get(normalized_host, []))


_global_mock_dns: Optional[MockDNSResolver] = None


def get_dns_resolver() -> BaseDNSResolver:
    """Factory returning configured DNS resolver based on application settings."""
    global _global_mock_dns
    import os

    current_settings = get_settings()
    env_mode = os.environ.get("DNS_RESOLVER_MODE")
    mode = (env_mode or current_settings.DNS_RESOLVER_MODE).lower()

    if current_settings.ENVIRONMENT.lower() == "production" and mode == "mock":
        raise ConfigurationError("Mock DNS resolver is strictly forbidden in production.")

    if mode == "mock":
        if _global_mock_dns is None:
            _global_mock_dns = MockDNSResolver()
        return _global_mock_dns
    return SystemDNSResolver()

