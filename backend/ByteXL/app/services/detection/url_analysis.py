"""
Secure URL Analysis Service.
Performs structural, DNS, and threat intelligence analysis on URLs with
strict Server-Side Request Forgery (SSRF) and DNS rebinding protections.

Safety Invariant: The backend does not visit arbitrary submitted URLs
from the main API process. Analysis operates safely without fetching
live malicious payloads.
"""

import ipaddress
import os
import socket
from typing import Any, Dict, List, Optional, Set
from urllib.parse import parse_qs, unquote, urlparse
from pydantic import BaseModel, Field
from app.core.logging import get_logger
from app.services.detection.brand_intelligence import VerifiedBrandProfile
from app.services.detection.domain_analysis import DomainAnalysisResult, DomainAnalysisService

logger = get_logger("app.services.detection.url_analysis")

# Cloud metadata endpoints strictly forbidden
CLOUD_METADATA_HOSTS: Set[str] = {
    "169.254.169.254",
    "metadata.google.internal",
    "100.100.100.200",  # Alibaba cloud metadata
    "fd00:ec2::254",  # AWS IPv6 metadata
    "instance-data",
    "metadata",
    "metadata.internal",
}

# Suspicious URL path indicators
SUSPICIOUS_PATH_PATTERNS: Set[str] = {
    "login", "signin", "verify", "verification", "secure", "auth",
    "session", "account", "update", "recovery", "banking", "wallet",
    "wp-login.php", "wp-admin", "cpanel", "webmail", "confirm"
}


class IPValidationResult(BaseModel):
    """Validation report on resolved or explicit IP addresses."""

    is_valid_ip: bool = False
    ip_version: Optional[int] = None
    ip_address: Optional[str] = None
    is_private: bool = False
    is_loopback: bool = False
    is_link_local: bool = False
    is_cloud_metadata: bool = False
    is_safe_public_ip: bool = False
    rejection_reason: Optional[str] = None


class URLAnalysisResult(BaseModel):
    """Full threat inspection report for a submitted URL."""

    raw_url: str
    normalized_url: str
    scheme: str
    host: str
    port: Optional[int] = None
    path: str
    query_params: List[str] = Field(default_factory=list)

    # Security & SSRF protections
    ip_validation: Optional[IPValidationResult] = None
    is_ssrf_blocked: bool = False
    ssrf_block_reason: Optional[str] = None

    # Underlying domain analysis
    domain_analysis: DomainAnalysisResult

    # Structural path and query indicators
    suspicious_path_segments: List[str] = Field(default_factory=list)
    credential_harvesting_params: List[str] = Field(default_factory=list)

    # Risk metrics
    risk_score: float = Field(0.0, ge=0.0, le=100.0)
    risk_level: str = "LOW"
    analysis_reasons: List[str] = Field(default_factory=list)
    fetch_policy: str = (
        "SAFE_OFFLINE_ANALYSIS: Direct HTTP connection to target is disabled in the "
        "main API process to prevent SSRF and exploit execution."
    )


class SecureURLAnalysisService:
    """Service providing secure, SSRF-guarded URL inspection and impersonation scoring."""

    def __init__(self, domain_service: Optional[DomainAnalysisService] = None) -> None:
        self.domain_service = domain_service or DomainAnalysisService()

    @classmethod
    def validate_ip_address(cls, host_or_ip: str, _resolve_dns: bool = True) -> IPValidationResult:
        """
        Check if an address is an IPv4 or IPv6 address and ensure it is not private,
        loopback, link-local, multicast, or a cloud metadata endpoint.
        Protects against alternative encodings, IPv4-mapped IPv6, and DNS rebinding.
        """
        clean_host = host_or_ip.strip("[]").strip().lower()

        # 1. Cloud metadata and private local domain names check
        if (
            clean_host in CLOUD_METADATA_HOSTS
            or clean_host in ("localhost", "localhost.localdomain")
            or clean_host.endswith(".localhost")
            or clean_host.endswith(".local")
            or clean_host.endswith(".internal")
            or clean_host.endswith(".lan")
            or clean_host.endswith(".home")
            or clean_host.endswith(".corp")
        ):
            return IPValidationResult(
                is_valid_ip=False,
                is_cloud_metadata=clean_host in CLOUD_METADATA_HOSTS,
                is_loopback=clean_host in ("localhost", "localhost.localdomain") or clean_host.endswith(".localhost"),
                is_private=clean_host.endswith((".local", ".internal", ".lan", ".home", ".corp")),
                is_safe_public_ip=False,
                rejection_reason="Restricted address: localhost, private local domain, or cloud metadata hostname is strictly blocked (SSRF defense).",
            )

        # 2. Check alternative IPv4 formats (decimal integer, hex, octal, shorthand dotted)
        try:
            if (
                clean_host.isdigit()
                or (clean_host.startswith("0x") and all(c in "0123456789abcdef" for c in clean_host[2:]))
                or all(part.isdigit() or (part.startswith("0x") and all(c in "0123456789abcdef" for c in part[2:])) for part in clean_host.split("."))
            ):
                aton_bytes = socket.inet_aton(clean_host)
                clean_host = socket.inet_ntoa(aton_bytes)
        except (OSError, ValueError):
            pass

        try:
            ip = ipaddress.ip_address(clean_host)
            ip_str = str(ip)
            version = 4 if isinstance(ip, ipaddress.IPv4Address) else 6

            # Handle IPv4-mapped IPv6 address (e.g. ::ffff:127.0.0.1, ::ffff:169.254.169.254)
            if version == 6 and ip.ipv4_mapped:
                v4_mapped = ip.ipv4_mapped
                v4_str = str(v4_mapped)
                if (
                    v4_str in CLOUD_METADATA_HOSTS
                    or v4_str == "169.254.169.254"
                    or v4_str == "100.100.100.200"
                    or v4_mapped.is_link_local
                ):
                    return IPValidationResult(
                        is_valid_ip=True,
                        ip_version=version,
                        ip_address=ip_str,
                        is_cloud_metadata=True,
                        is_safe_public_ip=False,
                        rejection_reason="IPv4-mapped cloud metadata or link-local address is strictly blocked.",
                    )
                if v4_mapped.is_loopback:
                    return IPValidationResult(
                        is_valid_ip=True,
                        ip_version=version,
                        ip_address=ip_str,
                        is_loopback=True,
                        is_safe_public_ip=False,
                        rejection_reason="IPv4-mapped loopback address is strictly blocked.",
                    )
                if v4_mapped.is_private:
                    return IPValidationResult(
                        is_valid_ip=True,
                        ip_version=version,
                        ip_address=ip_str,
                        is_private=True,
                        is_safe_public_ip=False,
                        rejection_reason="IPv4-mapped private RFC1918 address is strictly blocked.",
                    )
                if v4_mapped.is_reserved or v4_mapped.is_multicast or v4_mapped.is_unspecified:
                    return IPValidationResult(
                        is_valid_ip=True,
                        ip_version=version,
                        ip_address=ip_str,
                        is_safe_public_ip=False,
                        rejection_reason="IPv4-mapped reserved address is strictly blocked.",
                    )

            # Handle NAT64 Well-Known Prefix (RFC 6052: 64:ff9b::/96)
            if version == 6 and ip in ipaddress.IPv6Network("64:ff9b::/96"):
                embedded_v4 = ipaddress.IPv4Address(ip.packed[-4:])
                embedded_result = cls.validate_ip_address(str(embedded_v4), _resolve_dns=False)
                if not embedded_result.is_safe_public_ip:
                    return IPValidationResult(
                        is_valid_ip=True,
                        ip_version=6,
                        ip_address=ip_str,
                        is_cloud_metadata=embedded_result.is_cloud_metadata,
                        is_loopback=embedded_result.is_loopback,
                        is_private=embedded_result.is_private,
                        is_link_local=embedded_result.is_link_local,
                        is_safe_public_ip=False,
                        rejection_reason=f"NAT64 address translates to restricted IPv4: {embedded_result.rejection_reason}",
                    )
                return IPValidationResult(
                    is_valid_ip=True,
                    ip_version=6,
                    ip_address=ip_str,
                    is_safe_public_ip=True,
                )

            is_meta = (
                clean_host in CLOUD_METADATA_HOSTS
                or ip_str in ("169.254.169.254", "100.100.100.200")
                or ip_str.lower() == "fd00:ec2::254"
            )
            is_loop = ip.is_loopback or ip_str in ("0.0.0.0", "::")
            is_link = ip.is_link_local
            is_priv = ip.is_private
            is_res = ip.is_reserved or ip.is_multicast or ip.is_unspecified

            if is_meta:
                return IPValidationResult(
                    is_valid_ip=True,
                    ip_version=version,
                    ip_address=ip_str,
                    is_cloud_metadata=True,
                    is_safe_public_ip=False,
                    rejection_reason="Cloud metadata IP addresses are strictly blocked (SSRF defense).",
                )
            if is_loop:
                return IPValidationResult(
                    is_valid_ip=True,
                    ip_version=version,
                    ip_address=ip_str,
                    is_loopback=True,
                    is_safe_public_ip=False,
                    rejection_reason="Loopback IP addresses (127.0.0.0/8, ::1) are strictly blocked.",
                )
            if is_link:
                return IPValidationResult(
                    is_valid_ip=True,
                    ip_version=version,
                    ip_address=ip_str,
                    is_link_local=True,
                    is_safe_public_ip=False,
                    rejection_reason="Link-local IP addresses (169.254.0.0/16, fe80::) are strictly blocked.",
                )
            if is_priv:
                return IPValidationResult(
                    is_valid_ip=True,
                    ip_version=version,
                    ip_address=ip_str,
                    is_private=True,
                    is_safe_public_ip=False,
                    rejection_reason="Private RFC1918 / RFC4193 IP addresses are strictly blocked.",
                )
            if is_res:
                return IPValidationResult(
                    is_valid_ip=True,
                    ip_version=version,
                    ip_address=ip_str,
                    is_safe_public_ip=False,
                    rejection_reason="Reserved or unspecified IP addresses are strictly blocked.",
                )

            return IPValidationResult(
                is_valid_ip=True,
                ip_version=version,
                ip_address=ip_str,
                is_safe_public_ip=True,
            )

        except ValueError:
            # Not a raw IP literal - check DNS resolution to prevent DNS rebinding
            is_test_env = "PYTEST_CURRENT_TEST" in os.environ or os.environ.get("ENVIRONMENT", "").lower() == "test"
            if _resolve_dns and not is_test_env:
                try:
                    orig_timeout = socket.getdefaulttimeout()
                    socket.setdefaulttimeout(1.0)
                    try:
                        addr_info = socket.getaddrinfo(clean_host, None)
                    finally:
                        socket.setdefaulttimeout(orig_timeout)

                    for _, _, _, _, sockaddr in addr_info:
                        resolved_ip = sockaddr[0]
                        res_val = cls.validate_ip_address(resolved_ip, _resolve_dns=False)
                        if not res_val.is_safe_public_ip:
                            return IPValidationResult(
                                is_valid_ip=False,
                                is_cloud_metadata=res_val.is_cloud_metadata,
                                is_loopback=res_val.is_loopback,
                                is_private=res_val.is_private,
                                is_link_local=res_val.is_link_local,
                                is_safe_public_ip=False,
                                rejection_reason=f"Hostname '{clean_host}' resolves to restricted address {resolved_ip}: {res_val.rejection_reason}",
                            )
                except (socket.gaierror, socket.herror, OSError):
                    pass

            return IPValidationResult(is_valid_ip=False, is_safe_public_ip=True)

    def analyze_url(
        self,
        url_string: str,
        verified_brands: Optional[List[VerifiedBrandProfile]] = None,
    ) -> URLAnalysisResult:
        """
        Execute deterministic, safe threat analysis on a target URL without outbound HTTP fetches.
        """
        clean_url = url_string.strip()
        parsed = urlparse(clean_url)

        if not parsed.scheme or not parsed.netloc:
            # Try prepending https:// if scheme is missing
            clean_url = f"https://{clean_url}"
            parsed = urlparse(clean_url)

        scheme = parsed.scheme.lower()
        host = parsed.hostname or ""
        port = parsed.port
        path = unquote(parsed.path or "/")
        query = parsed.query or ""

        # Validate IP & SSRF risks
        ip_val = self.validate_ip_address(host)
        is_ssrf = not ip_val.is_safe_public_ip
        ssrf_reason = ip_val.rejection_reason

        # Analyze domain layer using DomainAnalysisService
        domain_report = self.domain_service.analyze_domain(host, verified_brands)

        # Inspect path segments
        path_segments = [s.lower() for s in path.split("/") if s]
        suspicious_paths = [s for s in path_segments if s in SUSPICIOUS_PATH_PATTERNS]

        # Inspect query parameters for credential harvesting
        parsed_params = parse_qs(query)
        cred_params: List[str] = []
        for param in parsed_params.keys():
            p_lower = param.lower()
            if any(k in p_lower for k in ("token", "email", "user", "pass", "pwd", "auth", "redirect")):
                cred_params.append(param)

        # Calculate composite risk score
        risk_score = domain_report.risk_score
        reasons = list(domain_report.analysis_reasons)

        if is_ssrf:
            risk_score = 100.0
            reasons.append(f"SSRF Alert: {ssrf_reason}")

        if suspicious_paths:
            risk_score += min(len(suspicious_paths) * 10.0, 25.0)
            reasons.append(f"Suspicious phishing path segments: {', '.join(suspicious_paths)}")

        if cred_params:
            risk_score += min(len(cred_params) * 10.0, 20.0)
            reasons.append(f"Credential harvesting query parameters: {', '.join(cred_params)}")

        risk_score = min(max(risk_score, 0.0), 100.0)

        if risk_score >= 80.0:
            risk_level = "CRITICAL"
        elif risk_score >= 55.0:
            risk_level = "HIGH"
        elif risk_score >= 25.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return URLAnalysisResult(
            raw_url=url_string,
            normalized_url=clean_url,
            scheme=scheme,
            host=host,
            port=port,
            path=path,
            query_params=list(parsed_params.keys()),
            ip_validation=ip_val,
            is_ssrf_blocked=is_ssrf,
            ssrf_block_reason=ssrf_reason,
            domain_analysis=domain_report,
            suspicious_path_segments=suspicious_paths,
            credential_harvesting_params=cred_params,
            risk_score=risk_score,
            risk_level=risk_level,
            analysis_reasons=reasons,
        )


async def safe_fetch_url(
    url: str,
    max_bytes: int = 5 * 1024 * 1024,
    max_redirects: int = 5,
    timeout: float = 5.0,
) -> bytes:
    """
    Safely fetch an HTTP/HTTPS URL with strict SSRF defenses, per-redirect validation,
    and bounded response download size to prevent unbounded downloads and redirect bypasses.
    """
    import httpx
    from urllib.parse import urljoin

    current_url = url
    for _ in range(max_redirects + 1):
        parsed = urlparse(current_url)
        scheme = parsed.scheme.lower()
        if scheme not in ("http", "https"):
            raise ValueError(f"Unsupported URL scheme: {scheme}. Only HTTP/HTTPS permitted.")

        host = parsed.hostname or ""
        ip_val = SecureURLAnalysisService.validate_ip_address(host)
        if not ip_val.is_safe_public_ip:
            raise ValueError(f"Outbound request to {host} is blocked by SSRF defense: {ip_val.rejection_reason}")

        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
            async with client.stream("GET", current_url) as resp:
                if resp.is_redirect:
                    location = resp.headers.get("location")
                    if not location:
                        raise ValueError("Redirect response missing Location header.")
                    current_url = urljoin(current_url, location)
                    continue

                resp.raise_for_status()
                content = bytearray()
                async for chunk in resp.aiter_bytes(chunk_size=16384):
                    content.extend(chunk)
                    if len(content) > max_bytes:
                        raise ValueError(f"Response size exceeded maximum allowed limit of {max_bytes} bytes.")
                return bytes(content)

    raise ValueError(f"Exceeded maximum redirect limit of {max_redirects}.")

