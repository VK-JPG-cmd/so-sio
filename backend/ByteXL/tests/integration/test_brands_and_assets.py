import base64
import uuid
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.enums import BrandVerificationStatus, UserRole
from app.models.user import User
from app.services.dns_resolver import MockDNSResolver
from app.services.otp_provider import MockOTPProvider


async def _setup_verified_brand(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_otp: MockOTPProvider,
    mock_dns: MockDNSResolver,
    phone_owner: str,
    biz_name: str,
    domain: str,
) -> tuple[str, str, str]:
    """Helper creating a verified brand and returning (owner_id, token_owner, brand_id)."""
    # 1. Login owner
    await client.post("/api/v1/auth/otp/start", json={"phone_number": phone_owner})
    code = mock_otp.get_last_code(phone_owner)
    res_owner = await client.post("/api/v1/auth/otp/verify", json={"phone_number": phone_owner, "code": code})
    owner_id = res_owner.json()["user"]["id"]
    token_owner = res_owner.json()["access_token"]

    # 2. Submit application
    app_res = await client.post(
        "/api/v1/brand-applications",
        headers={"Authorization": f"Bearer {token_owner}"},
        json={"business_name": biz_name, "official_domain": domain},
    )
    app_id = app_res.json()["id"]

    # 3. DNS challenge & verify
    c_res = await client.post(
        f"/api/v1/brand-applications/{app_id}/domain-challenge",
        headers={"Authorization": f"Bearer {token_owner}"},
    )
    mock_dns.set_txt_records(c_res.json()["record_host"], [c_res.json()["expected_record_value"]])
    await client.post(
        f"/api/v1/brand-applications/{app_id}/verify-domain",
        headers={"Authorization": f"Bearer {token_owner}"},
        json={"token": c_res.json()["challenge_token"]},
    )

    # 4. Admin approval
    phone_admin = f"+1415555{uuid.uuid4().int % 9000 + 1000}"
    await client.post("/api/v1/auth/otp/start", json={"phone_number": phone_admin})
    code_admin = mock_otp.get_last_code(phone_admin)
    res_admin = await client.post("/api/v1/auth/otp/verify", json={"phone_number": phone_admin, "code": code_admin})
    admin_id = res_admin.json()["user"]["id"]
    token_admin = res_admin.json()["access_token"]

    await db_session.execute(
        update(User).where(User.id == uuid.UUID(admin_id)).values(role=UserRole.ADMIN)
    )
    await db_session.commit()

    rev_res = await client.post(
        f"/api/v1/admin/brand-applications/{app_id}/review",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={"decision": "APPROVE"},
    )
    brand_id = rev_res.json()["brand_id"]
    return owner_id, token_owner, brand_id


async def test_public_brand_discovery_and_privacy(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_otp: MockOTPProvider,
    mock_dns: MockDNSResolver,
) -> None:
    """Verify public brand endpoints return only safe metadata and never leak owner identity."""
    _, _, brand_id = await _setup_verified_brand(
        client, db_session, mock_otp, mock_dns,
        phone_owner="+14155555001",
        biz_name="Stark Industries",
        domain="starkindustries.com",
    )

    # Public list
    list_res = await client.get("/api/v1/brands")
    assert list_res.status_code == 200
    brands = list_res.json()
    assert len(brands) >= 1

    matched = [b for b in brands if b["id"] == brand_id][0]
    assert matched["display_name"] == "Stark Industries"
    assert matched["official_domain"] == "starkindustries.com"
    assert matched["verification_status"] == "VERIFIED"
    assert "created_at" in matched

    # Verify absence of private fields
    assert "owner_user_id" not in matched
    assert "phone" not in str(matched).lower()
    assert "token" not in str(matched).lower()

    # Public single brand lookup
    single_res = await client.get(f"/api/v1/brands/{brand_id}")
    assert single_res.status_code == 200
    sdata = single_res.json()
    assert sdata["display_name"] == "Stark Industries"
    assert "owner_user_id" not in sdata


async def test_brand_asset_metadata_management(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_otp: MockOTPProvider,
    mock_dns: MockDNSResolver,
) -> None:
    """Verify asset registration computes content hash, safe storage key, and enforces ownership."""
    _, token_owner, brand_id = await _setup_verified_brand(
        client, db_session, mock_otp, mock_dns,
        phone_owner="+14155555002",
        biz_name="Wayne Enterprises",
        domain="waynecorp.com",
    )

    sample_content = b"fake-png-binary-content-for-logo"
    content_b64 = base64.b64encode(sample_content).decode("utf-8")

    # 1. Owner registers brand logo (filename with directory traversal attempt)
    asset_res = await client.post(
        f"/api/v1/brands/{brand_id}/assets",
        headers={"Authorization": f"Bearer {token_owner}"},
        json={
            "asset_type": "LOGO",
            "filename": "../../../etc/logo.png",
            "content_base64": content_b64,
        },
    )
    assert asset_res.status_code == 201
    adata = asset_res.json()
    assert adata["asset_type"] == "LOGO"
    assert adata["brand_id"] == brand_id
    assert adata["content_hash"] is not None
    # Verify path traversal was sanitized out
    assert "../" not in adata["storage_key"]
    assert adata["storage_key"].startswith(f"brands/{brand_id}/assets/")

    # 2. Owner lists assets
    list_assets_res = await client.get(
        f"/api/v1/brands/{brand_id}/assets",
        headers={"Authorization": f"Bearer {token_owner}"},
    )
    assert list_assets_res.status_code == 200
    assets = list_assets_res.json()
    assert len(assets) == 1
    assert assets[0]["id"] == adata["id"]

    # 3. Another user attempts to register or view assets -> 403 Forbidden
    await client.post("/api/v1/auth/otp/start", json={"phone_number": "+14155555003"})
    code_other = mock_otp.get_last_code("+14155555003")
    res_other = await client.post("/api/v1/auth/otp/verify", json={"phone_number": "+14155555003", "code": code_other})
    token_other = res_other.json()["access_token"]

    unauth_upload = await client.post(
        f"/api/v1/brands/{brand_id}/assets",
        headers={"Authorization": f"Bearer {token_other}"},
        json={"asset_type": "LOGO", "filename": "hack.png", "content_base64": content_b64},
    )
    assert unauth_upload.status_code == 403

    unauth_list = await client.get(
        f"/api/v1/brands/{brand_id}/assets",
        headers={"Authorization": f"Bearer {token_other}"},
    )
    assert unauth_list.status_code == 403
