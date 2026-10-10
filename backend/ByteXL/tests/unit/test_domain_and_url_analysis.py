"""
Unit tests for domain and URL security analysis:
- RapidFuzz similarity calculations
- Domain normalization
- Unicode confusable and homoglyph detection
- SSRF defenses (private IPs, loopback, link-local, cloud metadata)
- Malicious input handling
"""

import uuid
import pytest
from app.services.detection.brand_intelligence import VerifiedBrandProfile
from app.services.detection.domain_analysis import DomainAnalysisService
from app.services.detection.homoglyphs import HomoglyphDetector
from app.services.detection.url_analysis import SecureURLAnalysisService


@pytest.fixture
def sample_verified_brand() -> VerifiedBrandProfile:
    """Fixture providing an authoritative reference profile for Acme Bank."""
    return VerifiedBrandProfile(
        brand_id=uuid.uuid4(),
        display_name="Acme Bank",
        official_domain="acmebank.com",
        known_names=["Acme Bank", "Acme Financial"],
        known_social_handles=["acmebank", "acmebanksupport"],
        approved_keywords=["acme", "bank", "acmebank"],
        logo_storage_keys=["brands/logos/acme.png"],
        logo_hashes=["8f8f8f8f8f8f8f8f"],
    )


def test_homoglyph_detection_cyrillic_lookalikes() -> None:
    """Verify Cyrillic lookalikes are detected and mapped to canonical ASCII equivalents."""
    # "pаypаl" with Cyrillic 'а' (U+0430)
    spoofed = "p\u0430yp\u0430l.com"
    has_homo, canonical, detected = HomoglyphDetector.analyze_string(spoofed)

    assert has_homo is True
    assert canonical == "paypal.com"
    assert len(detected) == 2
    assert detected[0]["confusable_char"] == "\u0430"
    assert detected[0]["latin_equivalent"] == "a"


def test_homoglyph_mixed_script_detection() -> None:
    """Verify mixed Latin and Cyrillic script strings are flagged."""
    # "apple" with Cyrillic 'е' (U+0435)
    mixed = "appl\u0435"
    assert HomoglyphDetector.detect_mixed_script(mixed) is True

    # Pure Latin
    pure_latin = "apple"
    assert HomoglyphDetector.detect_mixed_script(pure_latin) is False


def test_domain_analysis_official_brand_domain(sample_verified_brand: VerifiedBrandProfile) -> None:
    """Verify exact official domain resolves to BENIGN with 0 risk score."""
    service = DomainAnalysisService()
    result = service.analyze_domain("acmebank.com", [sample_verified_brand])

    assert result.is_official_domain is True
    assert result.risk_score == 0.0
    assert result.risk_level == "BENIGN"
    assert result.matched_brand_name == "Acme Bank"


def test_domain_analysis_phishing_typosquatting(sample_verified_brand: VerifiedBrandProfile) -> None:
    """Verify typosquatted domain with phishing keywords receives HIGH/CRITICAL risk."""
    service = DomainAnalysisService()
    # Combines brand name with suspicious keywords
    result = service.analyze_domain("acmebank-login-verify.com", [sample_verified_brand])

    assert result.is_official_domain is False
    assert result.similarity_score > 60.0
    assert "login" in result.suspicious_keywords_found
    assert "verify" in result.suspicious_keywords_found
    assert result.risk_score >= 55.0
    assert result.risk_level in ("HIGH", "CRITICAL")


def test_domain_analysis_homoglyph_spoofing(sample_verified_brand: VerifiedBrandProfile) -> None:
    """Verify IDN homoglyph spoof domain is flagged with high risk."""
    service = DomainAnalysisService()
    # "acmebаnk.com" with Cyrillic 'а'
    homo_domain = "acmeb\u0430nk.com"
    result = service.analyze_domain(homo_domain, [sample_verified_brand])

    assert result.has_homoglyphs is True
    assert result.canonical_ascii_domain == "acmebank.com"
    assert result.risk_score >= 50.0


def test_domain_analysis_threat_intel_match() -> None:
    """Verify domain matching threat intelligence feed triggers critical alert."""
    custom_feed = {"known-c2-malware.com"}
    service = DomainAnalysisService(threat_intel_feed=custom_feed)

    result = service.analyze_domain("known-c2-malware.com")
    assert result.threat_intel_match is True
    assert result.risk_score >= 90.0
    assert result.risk_level == "CRITICAL"


def test_url_analysis_blocks_private_and_loopback_ips() -> None:
    """Verify SSRF defenses block private RFC1918 and loopback IPs."""
    # Loopback
    r_loop = SecureURLAnalysisService.validate_ip_address("127.0.0.1")
    assert r_loop.is_safe_public_ip is False
    assert r_loop.is_loopback is True

    # RFC1918 Private
    r_priv1 = SecureURLAnalysisService.validate_ip_address("10.0.0.1")
    assert r_priv1.is_safe_public_ip is False
    assert r_priv1.is_private is True

    r_priv2 = SecureURLAnalysisService.validate_ip_address("192.168.1.100")
    assert r_priv2.is_safe_public_ip is False
    assert r_priv2.is_private is True

    r_priv3 = SecureURLAnalysisService.validate_ip_address("172.16.5.20")
    assert r_priv3.is_safe_public_ip is False
    assert r_priv3.is_private is True

    # IPv6 loopback
    r_loop6 = SecureURLAnalysisService.validate_ip_address("::1")
    assert r_loop6.is_safe_public_ip is False
    assert r_loop6.is_loopback is True


def test_url_analysis_blocks_cloud_metadata_and_link_local() -> None:
    """Verify SSRF defenses block link-local and cloud metadata addresses."""
    # AWS / GCP metadata IP
    r_meta = SecureURLAnalysisService.validate_ip_address("169.254.169.254")
    assert r_meta.is_safe_public_ip is False
    assert r_meta.is_cloud_metadata is True

    # Cloud metadata hostname
    r_host = SecureURLAnalysisService.validate_ip_address("metadata.google.internal")
    assert r_host.is_safe_public_ip is False
    assert r_host.is_cloud_metadata is True

    # Link-local
    r_link = SecureURLAnalysisService.validate_ip_address("169.254.10.20")
    assert r_link.is_safe_public_ip is False
    assert (r_link.is_link_local or r_link.is_cloud_metadata) is True


def test_url_analysis_detects_credential_harvesting_params() -> None:
    """Verify URL query parameters containing credentials or redirects are detected."""
    service = SecureURLAnalysisService()
    test_url = "https://phishing-site.org/auth/verify?token=xyz123&user_email=victim@example.com&redirect_to=http://bad.com"

    result = service.analyze_url(test_url)
    assert len(result.credential_harvesting_params) >= 2
    assert "token" in result.credential_harvesting_params
    assert "user_email" in result.credential_harvesting_params
    assert "redirect_to" in result.credential_harvesting_params
