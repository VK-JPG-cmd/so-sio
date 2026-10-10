from httpx import AsyncClient
from app.services.otp_provider import MockOTPProvider


async def test_token_refresh_rotation_lifecycle(
    client: AsyncClient, mock_otp: MockOTPProvider
) -> None:
    """Verify refresh token rotation issues new pairs and revokes old tokens."""
    phone = "+14155552001"
    await client.post("/api/v1/auth/otp/start", json={"phone_number": phone})
    code = mock_otp.get_last_code(phone)

    login_res = await client.post(
        "/api/v1/auth/otp/verify",
        json={"phone_number": phone, "code": code},
    )
    assert login_res.status_code == 200
    first_refresh = login_res.json()["refresh_token"]

    # Rotate refresh token
    refresh_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": first_refresh},
    )
    assert refresh_res.status_code == 200
    second_refresh = refresh_res.json()["refresh_token"]
    assert second_refresh != first_refresh

    # Attempting to reuse old refresh token must be rejected
    reuse_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": first_refresh},
    )
    assert reuse_res.status_code == 401
    assert "Invalid or revoked refresh token" in reuse_res.json()["error"]["message"]


async def test_logout_endpoint_revokes_token(
    client: AsyncClient, mock_otp: MockOTPProvider
) -> None:
    """Verify logout revokes the user refresh token."""
    phone = "+14155552002"
    await client.post("/api/v1/auth/otp/start", json={"phone_number": phone})
    code = mock_otp.get_last_code(phone)

    login_res = await client.post(
        "/api/v1/auth/otp/verify",
        json={"phone_number": phone, "code": code},
    )
    assert login_res.status_code == 200
    data = login_res.json()
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]

    # Call logout with authorization header and body
    logout_res = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"refresh_token": refresh_token},
    )
    assert logout_res.status_code == 200
    assert logout_res.json()["message"] == "Successfully logged out."

    # Verify refresh token is revoked
    refresh_attempt = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_attempt.status_code == 401
