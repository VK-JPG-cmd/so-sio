from datetime import timedelta
import uuid
import jwt
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.core.security import create_access_token
from app.models.enums import AccountStatus, UserRole
from app.models.user import User
from app.services.otp_provider import MockOTPProvider

settings = get_settings()


async def test_get_my_profile_success(client: AsyncClient, mock_otp: MockOTPProvider) -> None:
    """Verify /users/me returns safe profile information for the authenticated user."""
    phone = "+14155553001"
    await client.post("/api/v1/auth/otp/start", json={"phone_number": phone})
    code = mock_otp.get_last_code(phone)

    login_res = await client.post(
        "/api/v1/auth/otp/verify",
        json={"phone_number": phone, "code": code},
    )
    token = login_res.json()["access_token"]

    me_res = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    data = me_res.json()
    assert data["phone_number"] == phone
    assert data["role"] == "CUSTOMER"
    assert data["account_status"] == "ACTIVE"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    # Ensure no secrets, tokens, or hashes are exposed
    assert "password" not in data
    assert "hash" not in str(data).lower()
    assert "salt" not in str(data).lower()


async def test_get_profile_unauthorized_without_token(client: AsyncClient) -> None:
    """Verify missing bearer token returns 401 Unauthorized."""
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_FAILED"


async def test_get_profile_with_invalid_or_tampered_jwt(client: AsyncClient) -> None:
    """Verify malformed or forged JWT signature returns 401 Unauthorized."""
    # Malformed token
    res1 = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer not-a-valid-token-format"},
    )
    assert res1.status_code == 401

    # Forged signature
    fake_token = jwt.encode(
        {"sub": str(uuid.uuid4()), "role": "ADMIN", "exp": 9999999999},
        "wrong-secret-key-that-does-not-match-settings",
        algorithm="HS256",
    )
    res2 = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {fake_token}"},
    )
    assert res2.status_code == 401
    assert "Invalid authentication token" in res2.json()["error"]["message"]


async def test_get_profile_with_expired_jwt(client: AsyncClient) -> None:
    """Verify expired access token is rejected with 401 Unauthorized."""
    expired_token, _ = create_access_token(
        user_id=uuid.uuid4(),
        role="CUSTOMER",
        expires_delta=timedelta(seconds=-10),  # expired 10 seconds ago
    )

    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert "expired" in response.json()["error"]["message"]


async def test_suspended_user_cannot_access_profile(
    client: AsyncClient, db_session: AsyncSession, mock_otp: MockOTPProvider
) -> None:
    """Verify a user whose status becomes SUSPENDED is blocked from protected routes."""
    phone = "+14155553002"
    await client.post("/api/v1/auth/otp/start", json={"phone_number": phone})
    code = mock_otp.get_last_code(phone)

    login_res = await client.post(
        "/api/v1/auth/otp/verify",
        json={"phone_number": phone, "code": code},
    )
    token = login_res.json()["access_token"]
    user_id = login_res.json()["user"]["id"]

    # Now suspend the user account in database
    await db_session.execute(
        update(User)
        .where(User.id == uuid.UUID(user_id))
        .values(account_status=AccountStatus.SUSPENDED)
    )
    await db_session.commit()

    # Attempt to access profile
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACCOUNT_SUSPENDED"


async def test_user_cannot_retrieve_another_user_private_profile(
    client: AsyncClient, mock_otp: MockOTPProvider
) -> None:
    """
    Verify identity boundary: User A cannot retrieve User B's profile.
    Data is isolated strictly by validated token.
    """
    phone_a = "+14155553003"
    phone_b = "+14155553004"

    # User A login
    await client.post("/api/v1/auth/otp/start", json={"phone_number": phone_a})
    code_a = mock_otp.get_last_code(phone_a)
    login_a = await client.post("/api/v1/auth/otp/verify", json={"phone_number": phone_a, "code": code_a})
    token_a = login_a.json()["access_token"]
    user_a_id = login_a.json()["user"]["id"]

    # User B login
    await client.post("/api/v1/auth/otp/start", json={"phone_number": phone_b})
    code_b = mock_otp.get_last_code(phone_b)
    login_b = await client.post("/api/v1/auth/otp/verify", json={"phone_number": phone_b, "code": code_b})
    token_b = login_b.json()["access_token"]
    user_b_id = login_b.json()["user"]["id"]

    # Request with Token A
    res_a = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a.json()["id"] == user_a_id
    assert res_a.json()["phone_number"] == phone_a
    assert res_a.json()["id"] != user_b_id

    # Request with Token B
    res_b = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b.json()["id"] == user_b_id
    assert res_b.json()["phone_number"] == phone_b


async def test_role_based_access_control(
    client: AsyncClient, db_session: AsyncSession, mock_otp: MockOTPProvider
) -> None:
    """
    Verify role enforcement:
    - Customer cannot access admin or brand owner endpoints.
    - Admin can access admin endpoints.
    - Brand owner can access brand owner endpoints.
    """
    # 1. Customer user
    phone_cust = "+14155553005"
    await client.post("/api/v1/auth/otp/start", json={"phone_number": phone_cust})
    code_cust = mock_otp.get_last_code(phone_cust)
    res_cust = await client.post("/api/v1/auth/otp/verify", json={"phone_number": phone_cust, "code": code_cust})
    token_cust = res_cust.json()["access_token"]

    # Customer tries admin endpoint -> 403
    cust_admin_res = await client.get(
        "/api/v1/users/admin-panel",
        headers={"Authorization": f"Bearer {token_cust}"},
    )
    assert cust_admin_res.status_code == 403
    assert cust_admin_res.json()["error"]["code"] == "ACCESS_FORBIDDEN"

    # Customer tries brand owner endpoint -> 403
    cust_brand_res = await client.get(
        "/api/v1/users/brand-portal",
        headers={"Authorization": f"Bearer {token_cust}"},
    )
    assert cust_brand_res.status_code == 403

    # 2. Promote user to ADMIN in database
    user_id = uuid.UUID(res_cust.json()["user"]["id"])
    await db_session.execute(
        update(User).where(User.id == user_id).values(role=UserRole.ADMIN)
    )
    await db_session.commit()

    # Now as ADMIN, accessing admin-panel succeeds
    admin_res = await client.get(
        "/api/v1/users/admin-panel",
        headers={"Authorization": f"Bearer {token_cust}"},
    )
    assert admin_res.status_code == 200
    assert admin_res.json()["role"] == "ADMIN"

    # 3. Create BRAND_OWNER user
    phone_brand = "+14155553006"
    await client.post("/api/v1/auth/otp/start", json={"phone_number": phone_brand})
    code_brand = mock_otp.get_last_code(phone_brand)
    res_b = await client.post("/api/v1/auth/otp/verify", json={"phone_number": phone_brand, "code": code_brand})
    token_brand = res_b.json()["access_token"]
    user_b_id = uuid.UUID(res_b.json()["user"]["id"])

    await db_session.execute(
        update(User).where(User.id == user_b_id).values(role=UserRole.BRAND_OWNER)
    )
    await db_session.commit()

    # Access brand portal -> 200
    brand_portal_res = await client.get(
        "/api/v1/users/brand-portal",
        headers={"Authorization": f"Bearer {token_brand}"},
    )
    assert brand_portal_res.status_code == 200
    assert brand_portal_res.json()["role"] == "BRAND_OWNER"

    # Brand owner cannot access admin panel -> 403
    brand_admin_res = await client.get(
        "/api/v1/users/admin-panel",
        headers={"Authorization": f"Bearer {token_brand}"},
    )
    assert brand_admin_res.status_code == 403
