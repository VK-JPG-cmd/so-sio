from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.enums import AccountStatus, UserRole
from app.models.otp import OTPVerification
from app.models.user import User
from app.services.otp_provider import MockOTPProvider


async def test_otp_start_success(client: AsyncClient, mock_otp: MockOTPProvider) -> None:
    """Verify requesting an OTP returns a security-preserving uniform response."""
    phone = "+14155551001"
    response = await client.post("/api/v1/auth/otp/start", json={"phone_number": phone})
    assert response.status_code == 200

    data = response.json()
    assert "verification code has been dispatched" in data["message"]
    assert data["cooldown_seconds"] == 60
    assert data["expires_in_seconds"] == 300

    # Ensure mock provider received an OTP without leaking it in the HTTP response
    code = mock_otp.get_last_code(phone)
    assert code is not None
    assert len(code) == 6
    assert code.isdigit()
    assert code not in response.text


async def test_otp_start_invalid_phone_rejected(client: AsyncClient) -> None:
    """Verify non-E.164 phone formats fail input validation with 422."""
    response = await client.post("/api/v1/auth/otp/start", json={"phone_number": "12345"})
    assert response.status_code == 422

    response_no_plus = await client.post("/api/v1/auth/otp/start", json={"phone_number": "14155551001"})
    assert response_no_plus.status_code == 422


async def test_otp_start_rate_limiting_cooldown(
    client: AsyncClient, mock_otp: MockOTPProvider
) -> None:
    """Verify requesting OTPs faster than cooldown window triggers 429 Too Many Requests."""
    phone = "+14155551002"
    first_res = await client.post("/api/v1/auth/otp/start", json={"phone_number": phone})
    assert first_res.status_code == 200

    # Immediate second request
    second_res = await client.post("/api/v1/auth/otp/start", json={"phone_number": phone})
    assert second_res.status_code == 429
    body = second_res.json()
    assert body["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert "cooldown_seconds" in body["error"]["details"]


async def test_otp_verify_valid_provisions_customer(
    client: AsyncClient, mock_otp: MockOTPProvider
) -> None:
    """Verify submitting valid OTP provisions a new user with CUSTOMER role and active tokens."""
    phone = "+14155551003"
    await client.post("/api/v1/auth/otp/start", json={"phone_number": phone})
    code = mock_otp.get_last_code(phone)
    assert code is not None

    verify_res = await client.post(
        "/api/v1/auth/otp/verify",
        json={"phone_number": phone, "code": code},
    )
    assert verify_res.status_code == 200

    data = verify_res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["phone_number"] == phone
    assert data["user"]["role"] == "CUSTOMER"
    assert data["user"]["account_status"] == "ACTIVE"
    assert data["user"]["phone_verified_at"] is not None


async def test_otp_verify_invalid_code(
    client: AsyncClient, mock_otp: MockOTPProvider
) -> None:
    """Verify submitting incorrect code decrements remaining attempts and returns 400."""
    phone = "+14155551004"
    await client.post("/api/v1/auth/otp/start", json={"phone_number": phone})

    verify_res = await client.post(
        "/api/v1/auth/otp/verify",
        json={"phone_number": phone, "code": "000000"},
    )
    assert verify_res.status_code == 400
    body = verify_res.json()
    assert body["error"]["code"] == "INVALID_OTP"
    assert "2 attempt(s) remaining" in body["error"]["message"]


async def test_otp_verify_repeated_failed_attempts_exhaustion(
    client: AsyncClient, mock_otp: MockOTPProvider
) -> None:
    """Verify 3 consecutive invalid attempts lock the OTP."""
    phone = "+14155551005"
    await client.post("/api/v1/auth/otp/start", json={"phone_number": phone})
    real_code = mock_otp.get_last_code(phone)

    # Attempt 1
    res1 = await client.post("/api/v1/auth/otp/verify", json={"phone_number": phone, "code": "111111"})
    assert res1.status_code == 400

    # Attempt 2
    res2 = await client.post("/api/v1/auth/otp/verify", json={"phone_number": phone, "code": "222222"})
    assert res2.status_code == 400

    # Attempt 3 (exhaustion)
    res3 = await client.post("/api/v1/auth/otp/verify", json={"phone_number": phone, "code": "333333"})
    assert res3.status_code == 400
    assert "Maximum attempts exceeded" in res3.json()["error"]["message"]

    # Even submitting the real code now must fail
    res4 = await client.post("/api/v1/auth/otp/verify", json={"phone_number": phone, "code": real_code})
    assert res4.status_code == 400
    assert "Maximum verification attempts exceeded" in res4.json()["error"]["message"]


async def test_otp_verify_expired_code(
    client: AsyncClient, db_session: AsyncSession, mock_otp: MockOTPProvider
) -> None:
    """Verify expired OTP code is rejected."""
    phone = "+14155551006"
    await client.post("/api/v1/auth/otp/start", json={"phone_number": phone})
    code = mock_otp.get_last_code(phone)

    # Force expiration in database
    past = datetime.now(timezone.utc) - timedelta(minutes=10)
    await db_session.execute(
        update(OTPVerification)
        .where(OTPVerification.phone_number == phone)
        .values(expires_at=past)
    )
    await db_session.commit()

    verify_res = await client.post(
        "/api/v1/auth/otp/verify",
        json={"phone_number": phone, "code": code},
    )
    assert verify_res.status_code == 400
    assert "expired" in verify_res.json()["error"]["message"]


async def test_otp_verify_cannot_reuse_used_code(
    client: AsyncClient, mock_otp: MockOTPProvider
) -> None:
    """Verify OTP cannot be reused once consumed."""
    phone = "+14155551007"
    await client.post("/api/v1/auth/otp/start", json={"phone_number": phone})
    code = mock_otp.get_last_code(phone)

    res1 = await client.post("/api/v1/auth/otp/verify", json={"phone_number": phone, "code": code})
    assert res1.status_code == 200

    res2 = await client.post("/api/v1/auth/otp/verify", json={"phone_number": phone, "code": code})
    assert res2.status_code == 400
    assert "No pending verification request" in res2.json()["error"]["message"]


async def test_otp_verify_suspended_account_rejected(
    client: AsyncClient, db_session: AsyncSession, mock_otp: MockOTPProvider
) -> None:
    """Verify OTP verification for a SUSPENDED account fails with 403 Forbidden."""
    phone = "+14155551008"

    # Pre-create suspended user
    user = User(
        phone_number=phone,
        role=UserRole.CUSTOMER,
        account_status=AccountStatus.SUSPENDED,
    )
    db_session.add(user)
    await db_session.commit()

    await client.post("/api/v1/auth/otp/start", json={"phone_number": phone})
    code = mock_otp.get_last_code(phone)

    verify_res = await client.post(
        "/api/v1/auth/otp/verify",
        json={"phone_number": phone, "code": code},
    )
    assert verify_res.status_code == 403
    assert verify_res.json()["error"]["code"] == "ACCOUNT_SUSPENDED"
