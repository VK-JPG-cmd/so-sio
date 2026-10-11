"""
SSL Certificate Validator.
Inspects domain SSL/TLS certificate chains, validates expiration,
verifies domain Subject Alternative Names (SAN), and scores reputable CAs vs self-signed.
"""

import asyncio
from datetime import datetime, timezone
import socket
import ssl
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger("app.services.brand_verification.ssl_validator")

TRUSTED_ENTERPRISE_CAS = {
    "DigiCert", "Sectigo", "Let's Encrypt", "Cloudflare", "GoDaddy",
    "Amazon", "Google Trust Services", "GlobalSign", "Entrust", "Comodo",
}


class SSLCertificateResult(BaseModel):
    domain: str
    is_valid: bool
    issuer: str
    common_name: Optional[str] = None
    san_list: List[str] = Field(default_factory=list)
    expires_at: Optional[str] = None
    is_trusted_ca: bool = False
    trust_score: float = Field(0.0, ge=0.0, le=100.0)
    error_message: Optional[str] = None


class SSLCertificateValidator:
    """Verifies domain ownership and authenticity via SSL certificate validation."""

    async def validate_brand_domain(self, domain: str) -> SSLCertificateResult:
        """
        1. Fetch SSL certificate chain
        2. Verify not expired
        3. Match domain against CN/SAN
        4. Score trusted CA vs self-signed/untrusted
        """
        clean_domain = domain.replace("https://", "").replace("http://", "").split("/")[0].split(":")[0]

        def _fetch_cert() -> SSLCertificateResult:
            ctx = ssl.create_default_context()
            ctx.timeout = 5.0
            try:
                with socket.create_connection((clean_domain, 443), timeout=5.0) as sock:
                    with ctx.wrap_socket(sock, server_hostname=clean_domain) as ssock:
                        cert = ssock.getpeercert()
                        issuer_dict = dict(x[0] for x in cert.get("issuer", []))
                        subject_dict = dict(x[0] for x in cert.get("subject", []))
                        issuer_org = issuer_dict.get("organizationName") or issuer_dict.get("commonName", "Known CA")
                        cn = subject_dict.get("commonName", clean_domain)
                        sans = [item[1] for item in cert.get("subjectAltName", []) if item[0] == "DNS"]
                        not_after = cert.get("notAfter", "")

                        # Trusted CA matching
                        is_trusted = any(ca.lower() in issuer_org.lower() for ca in TRUSTED_ENTERPRISE_CAS)
                        score = 95.0 if is_trusted else 75.0

                        return SSLCertificateResult(
                            domain=clean_domain,
                            is_valid=True,
                            issuer=issuer_org,
                            common_name=cn,
                            san_list=sans,
                            expires_at=not_after,
                            is_trusted_ca=is_trusted,
                            trust_score=score,
                        )
            except Exception as e:
                return SSLCertificateResult(
                    domain=clean_domain,
                    is_valid=False,
                    issuer="Untrusted / Self-Signed",
                    trust_score=20.0,
                    error_message=str(e),
                )

        return await asyncio.to_thread(_fetch_cert)
