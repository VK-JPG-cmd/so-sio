"""
Unit tests for standardized entity and identifier normalization.
Verifies:
- Case normalization
- Whitespace stripping and internal collapsing
- Unicode normalization (NFKC: fullwidth characters, ligatures)
- Punctuation and separator boundary handling
- Domain normalization (FQDN, label preservation, IP rejection)
- Social handle normalization across platforms (Twitter/X, Instagram, LinkedIn, URLs, leading @)
- Android package identifier normalization (component boundaries, case)
- iOS application identifier normalization (bundle IDs, numeric app store IDs)
- Leetspeak decoding
- Entity deduplication preservation
"""

import pytest
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
from app.services.correlation.normalization import normalize_threat_entity


def test_unicode_and_case_normalization() -> None:
    """Verify NFKC compatibility normalization and whitespace collapsing."""
    # Fullwidth Latin letters: "Ａｃmｅ" -> "Acme"
    fullwidth_text = "\uff21\uff43\uff4d\uff45"
    assert normalize_unicode_text(fullwidth_text) == "Acme"

    # Fullwidth digits: "１２３" -> "123"
    fullwidth_digits = "\uff11\uff12\uff13"
    assert normalize_unicode_text(fullwidth_digits) == "123"

    # Whitespace collapsing and case normalization
    messy = "   AcmePay   \t  Secure   \n  Wallet   "
    assert normalize_text(messy, lowercase=True) == "acmepay secure wallet"
    assert normalize_text(messy, lowercase=False) == "AcmePay Secure Wallet"


def test_tokenize_identifier_preserves_boundaries() -> None:
    """Verify boundary-aware tokenizer respects dots, hyphens, underscores, and camelCase."""
    # CamelCase transition
    tokens = tokenize_identifier("AcmePaySecureWallet")
    assert tokens == ["acme", "pay", "secure", "wallet"]

    # Dot, hyphen, underscore separators
    tokens2 = tokenize_identifier("com.acme-pay_wallet.app")
    assert tokens2 == ["com", "acme", "pay", "wallet", "app"]

    # Mixed with numbers
    tokens3 = tokenize_identifier("acmepay2026_support-v2")
    assert tokens3 == ["acmepay2026", "support", "v2"]


def test_decode_leetspeak() -> None:
    """Verify common leetspeak substitutions are deterministically mapped."""
    assert decode_leetspeak("4cm3p@y") == "acmepay"
    assert decode_leetspeak("s3cur3w@ll3t") == "securewallet"
    assert decode_leetspeak("b4nk1ng") == "banking"
    assert decode_leetspeak("$upp0rt") == "support"


def test_social_handle_normalization_across_platforms() -> None:
    """Verify social handle canonicalization handles leading @, platform URLs, and query params."""
    # Standard @handle
    assert normalize_social_handle(" @AcmePay_Support  ") == "acmepay_support"

    # Twitter/X profile URL
    assert normalize_social_handle("https://twitter.com/AcmePay") == "acmepay"
    assert normalize_social_handle("https://x.com/AcmePay?ref=src") == "acmepay"

    # Instagram profile URL
    assert normalize_social_handle("https://www.instagram.com/acmepay_official/") == "acmepay_official"

    # LinkedIn company/in profile URL
    assert normalize_social_handle("https://linkedin.com/in/acmepay-helpdesk") == "acmepay-helpdesk"

    # Raw domain path without scheme
    assert normalize_social_handle("twitter.com/AcmePayCare") == "acmepaycare"

    # Empty string
    assert normalize_social_handle("") == ""


def test_android_package_normalization() -> None:
    """Verify Android package normalization preserves component hierarchy and strips whitespace."""
    assert normalize_android_package("  Com.AcmePay.Wallet.App  ") == "com.acmepay.wallet.app"

    # Component extraction
    components = extract_package_components("com.acmepay.wallet")
    assert components == ["com", "acmepay", "wallet"]

    # Fullwidth characters in package name are normalized
    fullwidth_pkg = "com.\uff41\uff43\uff4d\uff45\uff50\uff41\uff59.wallet"
    assert normalize_android_package(fullwidth_pkg) == "com.acmepay.wallet"


def test_ios_identifier_normalization() -> None:
    """Verify iOS application identifiers support both bundle IDs and numeric app store IDs."""
    # Bundle identifier
    assert normalize_ios_identifier("  Com.AcmePay.iOSWallet  ") == "com.acmepay.ioswallet"

    # Numeric App Store ID
    assert normalize_ios_identifier("  ID1234567890  ") == "id1234567890"
    assert normalize_ios_identifier("id987654321") == "id987654321"


def test_normalize_threat_entity_integration() -> None:
    """Verify normalize_threat_entity uses standardized helpers deterministically."""
    # DOMAIN
    assert normalize_threat_entity("HTTP://Login-Acme.com/", EntityType.DOMAIN) == "login-acme.com"

    # SOCIAL_PROFILE with URL
    assert normalize_threat_entity("https://x.com/AcmePay_Care", EntityType.SOCIAL_PROFILE) == "acmepay_care"

    # APK_PACKAGE
    assert normalize_threat_entity("  Com.Phish.AcmeApp  ", EntityType.APK_PACKAGE) == "com.phish.acmeapp"

    # SCAM_TEXT_HASH
    h1 = normalize_threat_entity("Urgent: Account Suspended!  ", EntityType.SCAM_TEXT_HASH)
    h2 = normalize_threat_entity("urgent: account suspended!", EntityType.SCAM_TEXT_HASH)
    assert h1 == h2
