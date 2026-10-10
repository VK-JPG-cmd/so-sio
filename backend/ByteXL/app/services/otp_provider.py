import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Optional
from twilio.base.exceptions import TwilioException, TwilioRestException
from twilio.rest import Client

from app.core.config import get_settings
from app.core.exceptions import ConfigurationError, OTPDeliveryError, OTPVerificationError
from app.core.logging import get_logger
from app.core.security import mask_phone_number

logger = get_logger("app.services.otp")
settings = get_settings()


class BaseOTPProvider(ABC):
    """Abstract base provider for OTP code delivery and verification."""

    @abstractmethod
    async def send_otp(self, phone_number: str, code: Optional[str] = None) -> bool:
        """
        Deliver OTP to destination phone number.
        Returns True on successful dispatch, raises exception otherwise.
        """
        pass

    @abstractmethod
    async def verify_otp(self, phone_number: str, code: str) -> bool:
        """
        Verify submitted OTP code for the phone number.
        Returns True if code is valid, False otherwise.
        """
        pass


class MockOTPProvider(BaseOTPProvider):
    """
    Mock OTP provider for local automated test suites.
    Never sends live carrier SMS and strictly prohibited in production.
    """

    def __init__(self) -> None:
        if settings.ENVIRONMENT.lower() == "production":
            raise ConfigurationError("MockOTPProvider cannot be initialized in production.")
        self.sent_codes: Dict[str, str] = {}
        logger.info("Initialized MockOTPProvider (testing mode).")

    async def send_otp(self, phone_number: str, code: Optional[str] = None) -> bool:
        actual_code = code or "123456"
        self.sent_codes[phone_number] = actual_code
        logger.debug(
            f"Mock OTP captured for {mask_phone_number(phone_number)} [length: {len(actual_code)}]"
        )
        return True

    async def verify_otp(self, phone_number: str, code: str) -> bool:
        expected = self.sent_codes.get(phone_number)
        if not expected:
            return False
        return expected.strip() == code.strip()

    def get_last_code(self, phone_number: str) -> Optional[str]:
        """Test fixture helper to inspect captured codes."""
        return self.sent_codes.get(phone_number)

    def clear(self) -> None:
        """Test fixture helper to clear in-memory state."""
        self.sent_codes.clear()


class ConsoleOTPProvider(BaseOTPProvider):
    """Development provider logging dispatch without sending real carrier SMS."""

    def __init__(self) -> None:
        if settings.ENVIRONMENT.lower() == "production":
            raise ConfigurationError("ConsoleOTPProvider cannot be initialized in production.")
        self.sent_codes: Dict[str, str] = {}

    async def send_otp(self, phone_number: str, code: Optional[str] = None) -> bool:
        actual_code = code or "123456"
        self.sent_codes[phone_number] = actual_code
        logger.info(
            f"Simulated SMS dispatch triggered for {mask_phone_number(phone_number)} -> [Console Provider]"
        )
        return True

    async def verify_otp(self, phone_number: str, code: str) -> bool:
        expected = self.sent_codes.get(phone_number)
        if not expected:
            return False
        return expected.strip() == code.strip()


class Fast2SMSProvider(BaseOTPProvider):
    """
    Indian SMS delivery provider using Fast2SMS Bulk V2 OTP API.
    Sends authentic SMS to any Indian mobile number without pre-verification.
    """

    def __init__(self) -> None:
        import os
        api_key = getattr(settings, "FAST2SMS_API_KEY", None) or os.environ.get("FAST2SMS_API_KEY")
        if not api_key:
            raise ConfigurationError(
                "FAST2SMS_API_KEY is required in backend/.env when OTP_PROVIDER is 'fast2sms'."
            )
        self.api_key = str(api_key).strip()
        logger.info("Initialized Fast2SMSProvider for live SMS delivery.")

    async def send_otp(self, phone_number: str, code: Optional[str] = None) -> bool:
        if not code:
            raise OTPDeliveryError("OTP code is required for Fast2SMS delivery.")

        import re
        import httpx

        digits = re.sub(r"\D", "", phone_number)
        if len(digits) > 10:
            digits = digits[-10:]
        if len(digits) != 10:
            raise OTPDeliveryError(
                f"Fast2SMS requires a valid 10-digit Indian mobile number, got '{phone_number}'."
            )

        masked = mask_phone_number(phone_number)
        logger.info(f"Dispatching Fast2SMS OTP challenge to destination: {masked}")

        url = "https://www.fast2sms.com/dev/bulkV2"
        headers = {
            "authorization": self.api_key,
            "Content-Type": "application/json",
        }

        # Try route 'q' (Quick SMS - does not require website verification)
        payload_q = {
            "route": "q",
            "message": f"Your So-cio verification code is: {code}. Valid for 5 minutes.",
            "flash": 0,
            "numbers": digits,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, headers=headers, json=payload_q)
                data = res.json()
                if res.status_code == 200 and data.get("return") is True:
                    logger.info(f"Fast2SMS OTP challenge successfully delivered via Quick SMS to {masked}")
                    return True

                # If route 'q' fails, fallback to route 'otp'
                logger.warning(f"Fast2SMS Quick SMS route failed, attempting route 'otp' for {masked}")
                payload_otp = {
                    "route": "otp",
                    "variables_values": str(code),
                    "numbers": digits,
                }
                res_otp = await client.post(url, headers=headers, json=payload_otp)
                data_otp = res_otp.json()
                if res_otp.status_code == 200 and data_otp.get("return") is True:
                    logger.info(f"Fast2SMS OTP challenge successfully delivered via route 'otp' to {masked}")
                    return True
                else:
                    msg = data_otp.get("message") or data.get("message", ["Fast2SMS dispatch rejected"])
                    if isinstance(msg, list):
                        msg = " ".join(msg)
                    logger.error(f"Fast2SMS dispatch rejected for {masked}: {msg}")
                    raise OTPDeliveryError(f"SMS Delivery Failed: {msg}")
        except Exception as exc:
            if isinstance(exc, OTPDeliveryError):
                raise
            logger.error(f"Fast2SMS network failure for {masked}: {exc}")
            raise OTPDeliveryError(f"SMS network delivery error: {str(exc)}")

    async def verify_otp(self, phone_number: str, code: str) -> bool:
        return True


class TwilioVerifyProvider(BaseOTPProvider):
    """
    Production SMS provider integrating with Twilio Verify API v2.
    Twilio Verify handles cryptographic OTP generation, carrier delivery routing,
    and authoritative verification check validation.
    """

    def __init__(self) -> None:
        is_valid, error_msg = settings.validate_twilio_verify_config()
        if not is_valid:
            logger.error(f"Twilio Verify configuration validation failed: {error_msg}")
            raise ConfigurationError(
                error_msg or "Invalid Twilio Verify configuration in environment variables."
            )

        self.account_sid = str(settings.TWILIO_ACCOUNT_SID).strip()
        self.api_key = settings.effective_twilio_api_key
        self.api_secret = str(settings.TWILIO_API_SECRET).strip() if settings.TWILIO_API_SECRET else None
        self.auth_token = str(settings.TWILIO_AUTH_TOKEN).strip() if settings.TWILIO_AUTH_TOKEN else None
        self.service_sid = str(settings.TWILIO_VERIFY_SERVICE_SID).strip()

        # Initialize Twilio Client with API Key & Secret or Auth Token
        if self.api_key and self.api_secret:
            self.client = Client(
                username=self.api_key,
                password=self.api_secret,
                account_sid=self.account_sid,
            )
        else:
            self.client = Client(
                username=self.account_sid,
                password=self.auth_token,
            )

        logger.info(
            f"Initialized TwilioVerifyProvider with Service SID ({self.service_sid[:4]}***) "
            f"and Account SID ({self.account_sid[:4]}***)."
        )

    async def send_otp(self, phone_number: str, code: Optional[str] = None) -> bool:
        """
        Request Twilio Verify to generate and deliver an OTP SMS to the phone number.
        """
        masked = mask_phone_number(phone_number)
        logger.info(f"Dispatching Twilio Verify SMS challenge to destination: {masked}")

        try:
            # Twilio Verify handles generating the code and carrier dispatch
            verification = await asyncio.to_thread(
                lambda: self.client.verify.v2.services(self.service_sid).verifications.create(
                    to=phone_number,
                    channel="sms",
                )
            )

            status_val = getattr(verification, "status", None)
            if status_val in ("pending", "approved"):
                logger.info(
                    f"Twilio Verify successfully accepted verification request for {masked} (Status: {status_val})"
                )
                return True
            else:
                logger.error(f"Twilio Verify returned non-pending status '{status_val}' for {masked}")
                raise OTPDeliveryError(
                    f"Twilio verification dispatch was not accepted (status: {status_val})."
                )

        except TwilioRestException as exc:
            safe_error = self._format_twilio_rest_error(exc)
            logger.error(
                f"Twilio API error during verification dispatch to {masked}: "
                f"HTTP {exc.status} (Twilio Code: {exc.code}) - {safe_error}"
            )
            raise OTPDeliveryError(safe_error)
        except Exception as exc:
            logger.error(f"Unexpected network error during Twilio verification dispatch to {masked}: {str(exc)}")
            raise OTPDeliveryError("SMS provider service is temporarily unreachable. Please try again shortly.")

    async def verify_otp(self, phone_number: str, code: str) -> bool:
        """
        Submit code to Twilio Verify for authoritative validation.
        """
        masked = mask_phone_number(phone_number)
        logger.info(f"Submitting Twilio Verify code check for {masked}")

        try:
            check = await asyncio.to_thread(
                lambda: self.client.verify.v2.services(self.service_sid).verification_checks.create(
                    to=phone_number,
                    code=code.strip(),
                )
            )

            status_val = getattr(check, "status", None)
            is_approved = (status_val == "approved")
            if is_approved:
                logger.info(f"Twilio Verify confirmed approved verification for {masked}")
            else:
                logger.warning(f"Twilio Verify rejected verification code for {masked} (Status: {status_val})")
            return is_approved

        except TwilioRestException as exc:
            # Twilio returns specific codes when code is invalid or attempts exhausted
            if exc.code == 60202:
                logger.warning(f"Twilio Verify maximum check attempts exceeded for {masked}")
                raise OTPVerificationError("Maximum verification attempts exceeded for this code. Please request a new code.")
            elif exc.code == 20404:
                logger.warning(f"Twilio Verify pending verification not found or expired for {masked}")
                return False
            else:
                safe_error = self._format_twilio_rest_error(exc)
                logger.error(f"Twilio API error during verification check for {masked}: {safe_error}")
                return False
        except Exception as exc:
            logger.error(f"Unexpected error checking verification code for {masked}: {str(exc)}")
            raise OTPVerificationError("Verification provider error. Please try again.")

    def _format_twilio_rest_error(self, exc: TwilioRestException) -> str:
        """Map Twilio API error codes into user-friendly, security-preserving explanations."""
        code = getattr(exc, "code", None)
        if code == 60200:
            return "Invalid phone number parameter provided to Twilio Verify."
        elif code == 60203:
            return "Max verification attempts reached for this mobile number. Please wait before retrying."
        elif code == 21211:
            return "The provided phone number is not a valid mobile number."
        elif code == 21608:
            return "Twilio Trial Restriction: Destination number is unverified in your Twilio Console."
        elif code == 21408:
            return "Twilio Regional Restriction: SMS delivery to this country is disabled in your Twilio Geo-Permissions."
        elif code in (20003, 8001):
            return "Twilio Authentication Failed: Please check TWILIO_ACCOUNT_SID, TWILIO_API_KEY, and TWILIO_API_SECRET."
        elif code == 20404:
            return "Twilio Verify Service SID not found. Please verify TWILIO_VERIFY_SERVICE_SID in .env."
        return f"Twilio SMS delivery failed (Error code {code or 'Provider'}: {getattr(exc, 'msg', 'Carrier error')})."


# Alias for backward compatibility
TwilioOTPProvider = TwilioVerifyProvider

_global_mock_provider: Optional[MockOTPProvider] = None


def get_otp_provider() -> BaseOTPProvider:
    """Factory returning configured OTP delivery provider based on settings."""
    global _global_mock_provider

    import os
    env = os.environ.get("ENVIRONMENT", settings.ENVIRONMENT).lower()
    provider_type = os.environ.get("OTP_PROVIDER", settings.OTP_PROVIDER).lower()

    if env == "production" and provider_type == "mock":
        raise ConfigurationError("Mock OTP provider is strictly prohibited in production.")

    if provider_type == "mock" or (env == "test" and provider_type != "twilio"):
        if _global_mock_provider is None:
            _global_mock_provider = MockOTPProvider()
        return _global_mock_provider
    elif provider_type == "console":
        return ConsoleOTPProvider()
    elif provider_type == "twilio":
        return TwilioVerifyProvider()
    elif provider_type == "fast2sms":
        return Fast2SMSProvider()
    else:
        raise ConfigurationError(f"Unsupported OTP provider: {provider_type}")
