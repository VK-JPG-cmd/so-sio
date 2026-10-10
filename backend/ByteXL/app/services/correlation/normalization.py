"""
Threat entity normalization and canonicalization.
Ensures deterministic deduplication across attack surfaces.
"""

import hashlib
import ipaddress
from urllib.parse import urlparse
from app.core.domain import normalize_domain
from app.core.normalization import (
    decode_leetspeak,
    extract_package_components,
    normalize_android_package,
    normalize_ios_identifier,
    normalize_social_handle,
    normalize_text,
    normalize_unicode_text,
    tokenize_identifier,
)
from app.models.enums import EntityType

# Re-export core normalizers for convenience
__all__ = [
    "normalize_threat_entity",
    "normalize_unicode_text",
    "normalize_text",
    "tokenize_identifier",
    "decode_leetspeak",
    "normalize_social_handle",
    "normalize_android_package",
    "normalize_ios_identifier",
    "extract_package_components",
]


def normalize_threat_entity(raw_value: str, entity_type: EntityType) -> str:
    """
    Produce a canonical, stripped, lowercase unique string for an entity.
    Guarantees deterministic entity deduplication.
    """
    raw = normalize_unicode_text(raw_value).strip()

    if entity_type == EntityType.DOMAIN:
        # Lowercase FQDN, strip scheme, trailing slash, path
        try:
            return normalize_domain(raw)
        except Exception:
            clean = raw.lower()
            if clean.startswith("http://") or clean.startswith("https://"):
                clean = urlparse(clean).netloc
            clean = clean.split("/")[0].split(":")[0]
            return clean.strip(".")

    elif entity_type == EntityType.URL:
        # Canonical URL without user-specific anchors/fragments
        clean = raw.strip()
        lower_clean = clean.lower()
        if not lower_clean.startswith(("http://", "https://")):
            clean = "http://" + clean
        parsed = urlparse(clean)
        scheme = parsed.scheme.lower()
        host = parsed.netloc.lower()
        path = (parsed.path or "/").lower()
        query = f"?{parsed.query}" if parsed.query else ""
        return f"{scheme}://{host}{path}{query}"

    elif entity_type == EntityType.IP_ADDRESS:
        # Validate and canonicalize IPv4 / IPv6 addresses
        try:
            parts = raw.split(".")
            clean_ip = (
                ".".join(str(int(p)) for p in parts)
                if len(parts) == 4 and all(p.isdigit() for p in parts)
                else raw
            )
            return str(ipaddress.ip_address(clean_ip).compressed)
        except Exception:
            return raw.lower().strip()

    elif entity_type == EntityType.SOCIAL_PROFILE:
        # Platform-aware canonical handle
        return normalize_social_handle(raw)

    elif entity_type == EntityType.SCAM_TEXT_HASH:
        # Standardize whitespace and compute SHA-256 fingerprint
        normalized_text = normalize_text(raw, lowercase=True)
        return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()

    elif entity_type == EntityType.IMAGE_HASH:
        # Lowercased hexadecimal perceptual hash
        return raw.lower().strip()

    elif entity_type == EntityType.APK_PACKAGE:
        # Lowercase Android package name (e.g., com.phish.app)
        return normalize_android_package(raw)

    return raw.lower().strip()
