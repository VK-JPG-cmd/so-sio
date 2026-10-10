"""
Comprehensive test suite for Twilio Verify Mobile OTP flow covering:
1. Valid phone-number format (E.164 via phonenumbers)
2. Invalid phone-number format rejection
3. Successful OTP send request through Twilio Verify (mocked)
4. Twilio credentials missing (safe ConfigurationError)
5. Twilio authentication failure handling
6. Twilio rejecting destination number
7. Twilio trial restrictions (code 21608 unverified number)
8. Successful OTP verification (approved check)
9. Incorrect OTP rejection
10. Expired OTP rejection
11. Too many verification attempts (attempt limit)
12. Repeated OTP requests (resend cooldown)
13. Twilio provider unavailable / network failure
14. OTP field initially empty in frontend component
15. No demo OTP in production frontend code
16. No automatic verification bypass in production flows
17. No protected session token before verification
18. No OTP or secrets in API responses
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from twilio.base.exceptions import TwilioRestException

from app.core.config import Settings
from app.core.exceptions import (
    ConfigurationError,
    OTPDeliveryError,
    OTPVerificationError,
    RateLimitExceededError,
)
from app.schemas.auth import (
    OTPStartRequest,
    OTPStartResponse,
    OTPVerifyRequest,
    normalize_phone_number,
)
from app.services.otp_provider import (
    MockOTPProvider,
    TwilioVerifyProvider,
)


# 1. Valid phone-number format (E.164)
def test_valid_phone_number_formatting() -> None:
    # Standard valid international numbers
    assert normalize_phone_number("+919876543210") == "+919876543210"
    assert normalize_phone_number("+14155552671") == "+14155552671"
    # Domestic 10-digit formats normalized with country code
    assert normalize_phone_number("9876543210") == "+919876543210"


# 2. Invalid phone-number format rejection
def test_invalid_phone_number_rejection() -> None:
    with pytest.raises(ValueError, match="not a valid|Unable to parse"):
        normalize_phone_number("12345")

    with pytest.raises(ValueError, match="not a valid|Unable to parse"):
        normalize_phone_number("+910000000000")

    with pytest.raises(ValueError, match="non-empty string"):
        normalize_phone_number("")


# 3. Successful OTP send request (mocked Twilio Verify)
@pytest.mark.asyncio
async def test_successful_twilio_verify_send() -> None:
    with patch("app.services.otp_provider.settings") as mock_settings:
        mock_settings.validate_twilio_verify_config.return_value = (True, None)
        mock_settings.TWILIO_ACCOUNT_SID = "AC_TEST_MOCK_ACCOUNT_SID"
        mock_settings.effective_twilio_api_key = "SK_TEST_MOCK_API_KEY"
        mock_settings.TWILIO_API_SECRET = "secret_key_12345678901234567890"
        mock_settings.TWILIO_AUTH_TOKEN = None
        mock_settings.TWILIO_VERIFY_SERVICE_SID = "VA_TEST_MOCK_VERIFY_SID"

        with patch("app.services.otp_provider.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client

            # Twilio verifications.create returns object with status='pending'
            mock_verif = MagicMock()
            mock_verif.status = "pending"
            mock_verif.sid = "VE123"
            mock_client.verify.v2.services.return_value.verifications.create.return_value = mock_verif

            provider = TwilioVerifyProvider()
            res = await provider.send_otp("+919876543210")
            assert res is True
            mock_client.verify.v2.services.return_value.verifications.create.assert_called_once_with(
                to="+919876543210",
                channel="sms",
            )


# 4. Twilio credentials missing
def test_twilio_credentials_missing() -> None:
    settings = Settings(
        TWILIO_ACCOUNT_SID=None,
        TWILIO_API_KEY=None,
        TWILIO_API_SECRET=None,
        TWILIO_VERIFY_SERVICE_SID=None,
    )
    is_valid, err = settings.validate_twilio_verify_config()
    assert is_valid is False
    assert "TWILIO_ACCOUNT_SID is required" in err


# 5. Twilio authentication failure (Error 20003 / 8001)
@pytest.mark.asyncio
async def test_twilio_auth_failure() -> None:
    with patch("app.services.otp_provider.settings") as mock_settings:
        mock_settings.validate_twilio_verify_config.return_value = (True, None)
        mock_settings.TWILIO_ACCOUNT_SID = "AC_TEST_MOCK_ACCOUNT_SID"
        mock_settings.effective_twilio_api_key = "SK_TEST_MOCK_API_KEY"
        mock_settings.TWILIO_API_SECRET = "secret"
        mock_settings.TWILIO_AUTH_TOKEN = None
        mock_settings.TWILIO_VERIFY_SERVICE_SID = "VA_TEST_MOCK_VERIFY_SID"

        with patch("app.services.otp_provider.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client

            twilio_err = TwilioRestException(
                status=401,
                uri="/v2/Services/VA123/Verifications",
                msg="Authenticate",
                code=20003,
            )
            mock_client.verify.v2.services.return_value.verifications.create.side_effect = twilio_err

            provider = TwilioVerifyProvider()
            with pytest.raises(OTPDeliveryError) as exc_info:
                await provider.send_otp("+919876543210")
            assert "Authentication Failed" in str(exc_info.value.message)


# 6. Twilio rejecting destination number (Error 21211)
@pytest.mark.asyncio
async def test_twilio_rejecting_destination_number() -> None:
    with patch("app.services.otp_provider.settings") as mock_settings:
        mock_settings.validate_twilio_verify_config.return_value = (True, None)
        mock_settings.TWILIO_ACCOUNT_SID = "AC_TEST_MOCK_ACCOUNT_SID"
        mock_settings.effective_twilio_api_key = "SK_TEST_MOCK_API_KEY"
        mock_settings.TWILIO_API_SECRET = "secret"
        mock_settings.TWILIO_AUTH_TOKEN = None
        mock_settings.TWILIO_VERIFY_SERVICE_SID = "VA_TEST_MOCK_VERIFY_SID"

        with patch("app.services.otp_provider.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client

            twilio_err = TwilioRestException(
                status=400,
                uri="/v2/Services/VA123/Verifications",
                msg="Invalid 'To' Phone Number",
                code=21211,
            )
            mock_client.verify.v2.services.return_value.verifications.create.side_effect = twilio_err

            provider = TwilioVerifyProvider()
            with pytest.raises(OTPDeliveryError) as exc_info:
                await provider.send_otp("+919876543210")
            assert "not a valid mobile number" in str(exc_info.value.message)


# 7. Twilio trial restrictions (Error 21608)
@pytest.mark.asyncio
async def test_twilio_trial_restriction_handling() -> None:
    with patch("app.services.otp_provider.settings") as mock_settings:
        mock_settings.validate_twilio_verify_config.return_value = (True, None)
        mock_settings.TWILIO_ACCOUNT_SID = "AC_TEST_MOCK_ACCOUNT_SID"
        mock_settings.effective_twilio_api_key = "SK_TEST_MOCK_API_KEY"
        mock_settings.TWILIO_API_SECRET = "secret"
        mock_settings.TWILIO_AUTH_TOKEN = None
        mock_settings.TWILIO_VERIFY_SERVICE_SID = "VA_TEST_MOCK_VERIFY_SID"

        with patch("app.services.otp_provider.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client

            twilio_err = TwilioRestException(
                status=400,
                uri="/v2/Services/VA123/Verifications",
                msg="Trial accounts cannot send messages to unverified numbers",
                code=21608,
            )
            mock_client.verify.v2.services.return_value.verifications.create.side_effect = twilio_err

            provider = TwilioVerifyProvider()
            with pytest.raises(OTPDeliveryError) as exc_info:
                await provider.send_otp("+919876543210")
            assert "Twilio Trial Restriction" in str(exc_info.value.message)


# 8. Successful OTP verification (Twilio status 'approved')
@pytest.mark.asyncio
async def test_successful_otp_verification() -> None:
    with patch("app.services.otp_provider.settings") as mock_settings:
        mock_settings.validate_twilio_verify_config.return_value = (True, None)
        mock_settings.TWILIO_ACCOUNT_SID = "AC_TEST_MOCK_ACCOUNT_SID"
        mock_settings.effective_twilio_api_key = "SK_TEST_MOCK_API_KEY"
        mock_settings.TWILIO_API_SECRET = "secret"
        mock_settings.TWILIO_AUTH_TOKEN = None
        mock_settings.TWILIO_VERIFY_SERVICE_SID = "VA_TEST_MOCK_VERIFY_SID"

        with patch("app.services.otp_provider.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client

            mock_check = MagicMock()
            mock_check.status = "approved"
            mock_check.sid = "VE_CHECK_123"
            mock_client.verify.v2.services.return_value.verification_checks.create.return_value = mock_check

            provider = TwilioVerifyProvider()
            result = await provider.verify_otp("+919876543210", "654321")
            assert result is True


# 9. Incorrect OTP rejection
@pytest.mark.asyncio
async def test_incorrect_otp_rejection() -> None:
    with patch("app.services.otp_provider.settings") as mock_settings:
        mock_settings.validate_twilio_verify_config.return_value = (True, None)
        mock_settings.TWILIO_ACCOUNT_SID = "AC_TEST_MOCK_ACCOUNT_SID"
        mock_settings.effective_twilio_api_key = "SK_TEST_MOCK_API_KEY"
        mock_settings.TWILIO_API_SECRET = "secret"
        mock_settings.TWILIO_AUTH_TOKEN = None
        mock_settings.TWILIO_VERIFY_SERVICE_SID = "VA_TEST_MOCK_VERIFY_SID"

        with patch("app.services.otp_provider.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client

            mock_check = MagicMock()
            mock_check.status = "pending"  # Twilio returns 'pending' when code is incorrect
            mock_client.verify.v2.services.return_value.verification_checks.create.return_value = mock_check

            provider = TwilioVerifyProvider()
            result = await provider.verify_otp("+919876543210", "000000")
            assert result is False


# 10. Expired OTP handling
@pytest.mark.asyncio
async def test_expired_otp_rejection() -> None:
    with patch("app.services.otp_provider.settings") as mock_settings:
        mock_settings.validate_twilio_verify_config.return_value = (True, None)
        mock_settings.TWILIO_ACCOUNT_SID = "AC_TEST_MOCK_ACCOUNT_SID"
        mock_settings.effective_twilio_api_key = "SK_TEST_MOCK_API_KEY"
        mock_settings.TWILIO_API_SECRET = "secret"
        mock_settings.TWILIO_AUTH_TOKEN = None
        mock_settings.TWILIO_VERIFY_SERVICE_SID = "VA_TEST_MOCK_VERIFY_SID"

        with patch("app.services.otp_provider.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client

            # When verification has expired, Twilio returns 404 / resource not found
            twilio_err = TwilioRestException(
                status=404,
                uri="/v2/Services/VA123/VerificationCheck",
                msg="Resource not found",
                code=20404,
            )
            mock_client.verify.v2.services.return_value.verification_checks.create.side_effect = twilio_err

            provider = TwilioVerifyProvider()
            result = await provider.verify_otp("+919876543210", "123456")
            assert result is False


# 11. Too many verification attempts (Error 60202)
@pytest.mark.asyncio
async def test_too_many_verification_attempts() -> None:
    with patch("app.services.otp_provider.settings") as mock_settings:
        mock_settings.validate_twilio_verify_config.return_value = (True, None)
        mock_settings.TWILIO_ACCOUNT_SID = "AC_TEST_MOCK_ACCOUNT_SID"
        mock_settings.effective_twilio_api_key = "SK_TEST_MOCK_API_KEY"
        mock_settings.TWILIO_API_SECRET = "secret"
        mock_settings.TWILIO_AUTH_TOKEN = None
        mock_settings.TWILIO_VERIFY_SERVICE_SID = "VA_TEST_MOCK_VERIFY_SID"

        with patch("app.services.otp_provider.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client

            twilio_err = TwilioRestException(
                status=429,
                uri="/v2/Services/VA123/VerificationCheck",
                msg="Max check attempts reached",
                code=60202,
            )
            mock_client.verify.v2.services.return_value.verification_checks.create.side_effect = twilio_err

            provider = TwilioVerifyProvider()
            with pytest.raises(OTPVerificationError, match="Maximum verification attempts exceeded"):
                await provider.verify_otp("+919876543210", "111111")


# 12. Repeated OTP requests (Resend cooldown)
@pytest.mark.asyncio
async def test_resend_cooldown_enforcement() -> None:
    mock_otp_repo = MagicMock()
    mock_active = MagicMock()
    mock_active.created_at = datetime.now(timezone.utc) - timedelta(seconds=2)
    mock_otp_repo.get_latest_active = AsyncMock(return_value=mock_active)

    from app.services.auth_service import AuthService
    auth_service = AuthService(otp_repo=mock_otp_repo)

    mock_db = AsyncMock()
    with pytest.raises(RateLimitExceededError, match="Please wait"):
        await auth_service.start_otp(mock_db, "+919876543210")


# 13. Twilio provider unavailable / network error
@pytest.mark.asyncio
async def test_twilio_provider_network_unavailable() -> None:
    with patch("app.services.otp_provider.settings") as mock_settings:
        mock_settings.validate_twilio_verify_config.return_value = (True, None)
        mock_settings.TWILIO_ACCOUNT_SID = "AC_TEST_MOCK_ACCOUNT_SID"
        mock_settings.effective_twilio_api_key = "SK_TEST_MOCK_API_KEY"
        mock_settings.TWILIO_API_SECRET = "secret"
        mock_settings.TWILIO_AUTH_TOKEN = None
        mock_settings.TWILIO_VERIFY_SERVICE_SID = "VA_TEST_MOCK_VERIFY_SID"

        with patch("app.services.otp_provider.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_client.verify.v2.services.return_value.verifications.create.side_effect = RuntimeError(
                "DNS lookup timeout"
            )

            provider = TwilioVerifyProvider()
            with pytest.raises(OTPDeliveryError, match="temporarily unreachable"):
                await provider.send_otp("+919876543210")


def _find_frontend_file(rel_path: str) -> Path:
    for p in Path(__file__).resolve().parents:
        cand = p / rel_path
        if cand.exists():
            return cand
    raise FileNotFoundError(f"Could not locate {rel_path}")


# 14. OTP field initially empty in frontend component
def test_frontend_otp_field_initially_empty() -> None:
    comp_path = _find_frontend_file("src/features/auth/PhoneOtpVerification.tsx")
    content = comp_path.read_text(encoding="utf-8")
    assert "const [otp, setOtp] = useState<string[]>(['', '', '', '', '', '']);" in content


# 15. No demo OTP in frontend code
def test_no_demo_otp_in_frontend() -> None:
    comp_path = _find_frontend_file("src/features/auth/PhoneOtpVerification.tsx")
    content = comp_path.read_text(encoding="utf-8")
    assert "currentDevCode" not in content
    assert "789012" not in content
    assert "Fill Code" not in content
    assert "Autofill" not in content


# 16. No automatic verification in frontend
def test_no_automatic_verification_bypass() -> None:
    auth_service_path = _find_frontend_file("src/services/api/authService.ts")
    content = auth_service_path.read_text(encoding="utf-8")
    assert "mock_jwt_token_customer" not in content
    assert "dev_code: '123456'" not in content


# 17. No protected session token before verification
def test_no_session_token_before_verification() -> None:
    # Verify OTPStartResponse has no access_token or token field
    fields = OTPStartResponse.model_fields.keys()
    assert "access_token" not in fields
    assert "token" not in fields
    assert "dev_code" not in fields


# 18. No OTP in API responses
def test_no_otp_in_api_responses() -> None:
    fields = OTPStartResponse.model_fields.keys()
    assert "code" not in fields
    assert "otp" not in fields
    assert "dev_code" not in fields
