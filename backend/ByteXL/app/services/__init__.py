"""Services package."""

from app.services.auth_service import AuthService
from app.services.brand_service import BrandService
from app.services.dns_resolver import (
    BaseDNSResolver,
    MockDNSResolver,
    SystemDNSResolver,
    get_dns_resolver,
)
from app.services.otp_provider import (
    BaseOTPProvider,
    ConsoleOTPProvider,
    MockOTPProvider,
    TwilioOTPProvider,
    get_otp_provider,
)

__all__ = [
    "AuthService",
    "BrandService",
    "BaseOTPProvider",
    "MockOTPProvider",
    "ConsoleOTPProvider",
    "TwilioOTPProvider",
    "get_otp_provider",
    "BaseDNSResolver",
    "SystemDNSResolver",
    "MockDNSResolver",
    "get_dns_resolver",
]
