import pytest
from app.core.domain import normalize_domain


def test_domain_normalization_success() -> None:
    """Verify various valid domain inputs are normalized into canonical lowercase FQDNs."""
    assert normalize_domain("EXAMPLE.COM") == "example.com"
    assert normalize_domain("  Acme.org  ") == "acme.org"
    assert normalize_domain("https://acme.org/") == "acme.org"
    assert normalize_domain("http://sub.brand.co.uk/portal") == "sub.brand.co.uk"
    assert normalize_domain("my-brand.store.") == "my-brand.store"
    assert normalize_domain("brand.ai:8080") == "brand.ai"


def test_domain_invalid_rejections() -> None:
    """Verify invalid domains, IP addresses, and malformed inputs are rejected."""
    # IP addresses
    with pytest.raises(ValueError) as exc_ip:
        normalize_domain("192.168.1.1")
    assert "IP address" in str(exc_ip.value)

    # Localhost / no TLD
    with pytest.raises(ValueError) as exc_local:
        normalize_domain("localhost")
    assert "not a valid domain" in str(exc_local.value)

    with pytest.raises(ValueError) as exc_notld:
        normalize_domain("brandname")
    assert "not a valid domain" in str(exc_notld.value)

    # Malformed syntax
    with pytest.raises(ValueError):
        normalize_domain("invalid..domain.com")

    with pytest.raises(ValueError):
        normalize_domain("exam!ple.com")

    with pytest.raises(ValueError):
        normalize_domain("")
