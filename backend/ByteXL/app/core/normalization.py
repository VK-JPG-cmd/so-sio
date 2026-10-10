"""
Standardized Threat Entity Normalization Utilities.
Provides deterministic, boundary-aware canonicalization across domains,
social handles, package identifiers, and general text.
"""

import re
import unicodedata
from typing import List, Optional
from urllib.parse import urlparse

# Characters commonly used as separators in identifiers
SEPARATOR_REGEX = re.compile(r"[-_.\s]+")

# Android Java package component regex
ANDROID_PACKAGE_REGEX = re.compile(
    r"^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)+$"
)

# iOS bundle ID regex or numeric app ID (e.g. id123456789)
IOS_IDENTIFIER_REGEX = re.compile(
    r"^(?:id\d{6,16}|[a-zA-Z0-9_-]+(?:\.[a-zA-Z0-9_-]+)+)$"
)

# Common leetspeak substitutions to standard Latin ASCII
LEETSPEAK_MAP = {
    "@": "a",
    "4": "a",
    "8": "b",
    "3": "e",
    "1": "i",
    "!": "i",
    "0": "o",
    "$": "s",
    "5": "s",
    "7": "t",
    "+": "t",
    "2": "z",
}


def normalize_unicode_text(text: str, form: str = "NFKC") -> str:
    """
    Apply standard Unicode normalization (default NFKC).
    Converts compatibility forms (fullwidth, ligatures, circled) to canonical ASCII/Latin.
    """
    if not text:
        return ""
    return unicodedata.normalize(form, text)


def normalize_text(text: str, lowercase: bool = True) -> str:
    """
    Normalize generic text: Unicode normalization, leading/trailing strip,
    whitespace collapsing, and optional lowercasing.
    """
    if not text:
        return ""
    norm = normalize_unicode_text(text)
    # Collapse multiple whitespaces
    norm = " ".join(norm.split())
    return norm.lower() if lowercase else norm


def tokenize_identifier(text: str) -> List[str]:
    """
    Boundary-aware tokenizer that splits on dots, hyphens, underscores,
    spaces, and camelCase transitions without losing token boundaries.
    """
    if not text:
        return []
    cleaned = normalize_unicode_text(text)
    # Insert boundary for camelCase transitions (e.g., AcmePay -> Acme Pay)
    camel_spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", cleaned)
    tokens = [t.lower() for t in SEPARATOR_REGEX.split(camel_spaced) if t]
    return tokens


def decode_leetspeak(text: str) -> str:
    """
    Deterministic mapping of common leetspeak substitutions to standard characters.
    """
    if not text:
        return ""
    norm = normalize_unicode_text(text)
    chars = [LEETSPEAK_MAP.get(c.lower(), c) for c in norm]
    return "".join(chars)


def normalize_social_handle(raw_handle: str, platform: Optional[str] = None) -> str:
    """
    Normalize social media account handles:
    - Strips URL schemes, domain prefixes (e.g. twitter.com/user, x.com/user, instagram.com/user)
    - Strips leading '@', trailing slashes, query parameters
    - Applies NFKC Unicode normalization and lowercasing
    - Preserves internal underscores and hyphens
    """
    if not raw_handle:
        return ""

    clean = raw_handle.strip()

    # Strip URL prefix if present
    if clean.lower().startswith(("http://", "https://", "www.")):
        parsed = urlparse(clean if clean.lower().startswith("http") else f"https://{clean}")
        path = parsed.path.strip("/")
        # If path has multiple segments, take the first valid handle segment
        segments = [s for s in path.split("/") if s and s.lower() not in ("in", "user", "channel", "c")]
        clean = segments[0] if segments else path

    # Strip platform domain if passed without scheme (e.g. twitter.com/handle)
    clean = re.sub(r"^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}/(?:in/|user/)?", "", clean)

    # Normalize unicode and lower
    clean = normalize_unicode_text(clean)
    clean = clean.lstrip("@").strip().lower()

    # Strip query parameters or fragments if accidentally remaining
    clean = clean.split("?")[0].split("#")[0].strip("/")
    return clean


def normalize_android_package(raw_package: str) -> str:
    """
    Normalize an Android package identifier:
    - Strips whitespace and applies Unicode normalization
    - Lowercases all component segments
    - Preserves dot-separated component hierarchy (e.g. com.acmepay.wallet)
    """
    if not raw_package:
        return ""
    clean = normalize_unicode_text(raw_package).strip().lower()
    return clean


def normalize_ios_identifier(raw_identifier: str) -> str:
    """
    Normalize an iOS application identifier:
    - Supports numeric store ID (e.g. id123456789 -> id123456789)
    - Supports bundle identifiers (e.g. com.acmepay.wallet -> com.acmepay.wallet)
    - Strips whitespace, applies Unicode normalization, lowercases
    """
    if not raw_identifier:
        return ""
    clean = normalize_unicode_text(raw_identifier).strip().lower()
    return clean


def extract_package_components(package_name: str) -> List[str]:
    """
    Split a package name into individual dot-separated components.
    e.g. 'com.acmepay.wallet' -> ['com', 'acmepay', 'wallet']
    """
    if not package_name:
        return []
    clean = normalize_android_package(package_name)
    return [c for c in clean.split(".") if c]
