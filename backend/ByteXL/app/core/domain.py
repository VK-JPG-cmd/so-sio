import re
from urllib.parse import urlparse

# Standard FQDN regex enforcing valid labels and TLD of at least 2 alpha characters
DOMAIN_REGEX = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}$"
)

# Detect IPv4 address
IPV4_REGEX = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")


def normalize_domain(raw_domain: str) -> str:
    """
    Validate and normalize a domain string into standard canonical lowercase FQDN.
    Strips schemes, trailing slashes, ports, and whitespace.
    Rejects IP addresses, localhost, and malformed characters.
    """
    if not raw_domain or not isinstance(raw_domain, str):
        raise ValueError("Domain must be a non-empty string.")

    cleaned = raw_domain.strip().lower()

    # Strip scheme if present
    if cleaned.startswith(("http://", "https://")):
        parsed = urlparse(cleaned)
        cleaned = parsed.netloc or parsed.path

    # Strip path or trailing slashes
    if "/" in cleaned:
        cleaned = cleaned.split("/", 1)[0]

    # Strip port if present
    if ":" in cleaned:
        cleaned = cleaned.split(":", 1)[0]

    # Strip trailing dot
    cleaned = cleaned.rstrip(".")

    # Reject localhost or single-label names
    if cleaned == "localhost" or "." not in cleaned:
        raise ValueError(f"'{raw_domain}' is not a valid domain. Must have a valid top-level domain.")

    # Reject IP addresses
    if IPV4_REGEX.match(cleaned):
        raise ValueError(f"IP address '{raw_domain}' is not permitted. Only fully qualified domain names are allowed.")

    # Validate syntax against FQDN regex
    if not DOMAIN_REGEX.match(cleaned):
        raise ValueError(f"'{raw_domain}' contains invalid characters or malformed domain structure.")

    return cleaned
