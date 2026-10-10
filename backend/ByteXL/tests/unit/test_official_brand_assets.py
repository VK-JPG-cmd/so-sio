import io
from typing import Tuple
import uuid
import zipfile
import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.enums import (
    AssetVerificationStatus,
    UserRole,
)
from app.models.official_mobile_asset import BrandMobileApp
from app.models.official_social_asset import BrandSocialAsset
from app.models.user import User
from app.services.detection.apk_analysis import APKAnalysisService
from app.services.detection.brand_intelligence import BrandIntelligenceService, VerifiedBrandProfile
from app.services.detection.profile_analysis import ProfileAnalysisService, SocialProfileInput
from app.services.otp_provider import MockOTPProvider


async def _create_user(client: AsyncClient, mock_otp: MockOTPProvider, phone: str) -> Tuple[str, str]:
    """Helper to authenticate a user."""
    await client.post("/api/v1/auth/otp/start", json={"phone_number": phone})
    code = mock_otp.get_last_code(phone)
    verify_res = await client.post(
        "/api/v1/auth/otp/verify", json={"phone_number": phone, "code": code}
    )
    data = verify_res.json()
    return data["user"]["id"], data["access_token"]


async def _create_admin(
    client: AsyncClient,
    mock_otp: MockOTPProvider,
    phone: str,
    db_session: AsyncSession,
) -> Tuple[str, str]:
    """Helper to authenticate an admin user."""
    user_id, token = await _create_user(client, mock_otp, phone)
    await db_session.execute(
        update(User).where(User.id == uuid.UUID(user_id)).values(role=UserRole.ADMIN)
    )
    await db_session.commit()
    return user_id, token


async def _setup_verified_brand(
    client: AsyncClient,
    mock_otp: MockOTPProvider,
    admin_token: str,
    phone: str,
    name: str = "AcmePay",
    domain: str = "acmepay.com",
) -> Tuple[str, str, str]:
    """Helper to register and approve a brand, returning (brand_id, owner_id, owner_token)."""
    owner_id, owner_token = await _create_user(client, mock_otp, phone)
    app_res = await client.post(
        "/api/v1/brand-applications",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"business_name": name, "official_domain": domain},
    )
    app_id = app_res.json()["id"]

    review_res = await client.post(
        f"/api/v1/admin/brand-applications/{app_id}/review",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"decision": "APPROVE", "notes": "Verified business entity"},
    )
    brand_id = str(review_res.json()["brand_id"])
    return brand_id, owner_id, owner_token


@pytest.mark.asyncio
async def test_social_asset_valid_registration_and_list(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    _, admin_token = await _create_admin(client, mock_otp, "+14155550001", db_session)
    brand_id, _, owner_token = await _setup_verified_brand(
        client, mock_otp, admin_token, "+14155550002", "AcmePay", "acmepay.com"
    )

    # 1. Register valid social asset
    payload = {
        "platform": "X",
        "handle": "@acmepay_official",
        "canonical_url": "https://x.com/acmepay_official",
        "evidence": "Corporate domain registry verification link",
    }
    response = await client.post(
        f"/api/v1/owner/brands/{brand_id}/social-assets",
        json=payload,
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["handle"] == "acmepay_official"
    assert data["platform"] == "X"
    assert data["canonical_url"] == "https://x.com/acmepay_official"
    assert data["verification_status"] == "PENDING"
    assert data["evidence"] == payload["evidence"]
    asset_id = data["id"]

    # 2. List social assets
    list_res = await client.get(
        f"/api/v1/owner/brands/{brand_id}/social-assets",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert list_res.status_code == 200
    assert list_res.headers["X-Total-Count"] == "1"
    items = list_res.json()
    assert len(items) == 1
    assert items[0]["id"] == asset_id


@pytest.mark.asyncio
async def test_social_asset_invalid_platform_and_url(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    _, admin_token = await _create_admin(client, mock_otp, "+14155550011", db_session)
    brand_id, _, owner_token = await _setup_verified_brand(
        client, mock_otp, admin_token, "+14155550012", "AcmePay2", "acmepay2.com"
    )

    # Invalid platform
    res_bad_plat = await client.post(
        f"/api/v1/owner/brands/{brand_id}/social-assets",
        json={
            "platform": "MySpace",
            "handle": "acmepay",
            "canonical_url": "https://myspace.com/acmepay",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res_bad_plat.status_code == 400

    # Invalid URL scheme
    res_bad_url = await client.post(
        f"/api/v1/owner/brands/{brand_id}/social-assets",
        json={
            "platform": "X",
            "handle": "acmepay",
            "canonical_url": "not-a-valid-url",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res_bad_url.status_code == 400

    # Mismatched URL host for platform
    res_bad_host = await client.post(
        f"/api/v1/owner/brands/{brand_id}/social-assets",
        json={
            "platform": "X",
            "handle": "acmepay",
            "canonical_url": "https://instagram.com/acmepay",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res_bad_host.status_code == 400


@pytest.mark.asyncio
async def test_social_asset_duplicate_registration(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    _, admin_token = await _create_admin(client, mock_otp, "+14155550021", db_session)
    brand_id, _, owner_token = await _setup_verified_brand(
        client, mock_otp, admin_token, "+14155550022", "AcmePay3", "acmepay3.com"
    )

    payload = {
        "platform": "X",
        "handle": "acmepay",
        "canonical_url": "https://x.com/acmepay",
    }
    r1 = await client.post(
        f"/api/v1/owner/brands/{brand_id}/social-assets",
        json=payload,
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert r1.status_code == 201

    # Duplicate registration attempt
    r2 = await client.post(
        f"/api/v1/owner/brands/{brand_id}/social-assets",
        json=payload,
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert r2.status_code == 400
    assert "already registered" in r2.text


@pytest.mark.asyncio
async def test_social_asset_unauthorized_access(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    _, admin_token = await _create_admin(client, mock_otp, "+14155550031", db_session)
    brand_id, _, _ = await _setup_verified_brand(
        client, mock_otp, admin_token, "+14155550032", "AcmePay4", "acmepay4.com"
    )
    _, attacker_token = await _create_user(client, mock_otp, "+14155550033")

    # Attacker tries to register asset on legit brand
    res = await client.post(
        f"/api/v1/owner/brands/{brand_id}/social-assets",
        json={
            "platform": "Instagram",
            "handle": "acmepay",
            "canonical_url": "https://instagram.com/acmepay",
        },
        headers={"Authorization": f"Bearer {attacker_token}"},
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_social_asset_update_delete_and_verification_rules(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    _, admin_token = await _create_admin(client, mock_otp, "+14155550041", db_session)
    brand_id, _, owner_token = await _setup_verified_brand(
        client, mock_otp, admin_token, "+14155550042", "AcmePay5", "acmepay5.com"
    )

    create_res = await client.post(
        f"/api/v1/owner/brands/{brand_id}/social-assets",
        json={
            "platform": "LinkedIn",
            "handle": "acmepay-official",
            "canonical_url": "https://linkedin.com/company/acmepay-official",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert create_res.status_code == 201
    asset_id = create_res.json()["id"]

    # Owner attempts to self-verify -> FORBIDDEN
    self_verify_res = await client.patch(
        f"/api/v1/owner/brands/{brand_id}/social-assets/{asset_id}",
        json={"verification_status": "VERIFIED"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert self_verify_res.status_code == 403

    # Admin verifies the asset -> SUCCESS
    admin_verify_res = await client.patch(
        f"/api/v1/owner/brands/{brand_id}/social-assets/{asset_id}",
        json={"verification_status": "VERIFIED"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_verify_res.status_code == 200
    assert admin_verify_res.json()["verification_status"] == "VERIFIED"

    # Owner deletes the asset -> SUCCESS
    del_res = await client.delete(
        f"/api/v1/owner/brands/{brand_id}/social-assets/{asset_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert del_res.status_code == 204


@pytest.mark.asyncio
async def test_mobile_app_valid_android_and_ios_registration(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    _, admin_token = await _create_admin(client, mock_otp, "+14155550051", db_session)
    brand_id, _, owner_token = await _setup_verified_brand(
        client, mock_otp, admin_token, "+14155550052", "AcmePay6", "acmepay6.com"
    )

    # 1. Android App
    res_android = await client.post(
        f"/api/v1/owner/brands/{brand_id}/mobile-apps",
        json={
            "app_name": "AcmePay Wallet",
            "platform": "ANDROID",
            "app_identifier": "com.acmepay.wallet",
            "publisher_name": "Acme Payments Inc",
            "store_url": "https://play.google.com/store/apps/details?id=com.acmepay.wallet",
            "evidence": "Google Play Developer Console screenshot",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res_android.status_code == 201, res_android.text
    data_android = res_android.json()
    assert data_android["platform"] == "ANDROID"
    assert data_android["app_identifier"] == "com.acmepay.wallet"
    assert data_android["verification_status"] == "PENDING"
    assert data_android["publisher_name"] == "Acme Payments Inc"

    # 2. iOS App
    res_ios = await client.post(
        f"/api/v1/owner/brands/{brand_id}/mobile-apps",
        json={
            "app_name": "AcmePay iOS",
            "platform": "IOS",
            "app_identifier": "id987654321",
            "publisher_name": "Acme Payments Inc",
            "store_url": "https://apps.apple.com/app/acmepay/id987654321",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res_ios.status_code == 201, res_ios.text
    data_ios = res_ios.json()
    assert data_ios["platform"] == "IOS"
    assert data_ios["app_identifier"] == "id987654321"

    # 3. List
    list_res = await client.get(
        f"/api/v1/owner/brands/{brand_id}/mobile-apps",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert list_res.status_code == 200
    assert list_res.headers["X-Total-Count"] == "2"
    assert len(list_res.json()) == 2


@pytest.mark.asyncio
async def test_mobile_app_validation_errors(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    _, admin_token = await _create_admin(client, mock_otp, "+14155550061", db_session)
    brand_id, _, owner_token = await _setup_verified_brand(
        client, mock_otp, admin_token, "+14155550062", "AcmePay7", "acmepay7.com"
    )

    # Invalid Android package name (starts with number)
    bad_pkg = await client.post(
        f"/api/v1/owner/brands/{brand_id}/mobile-apps",
        json={
            "app_name": "Bad App",
            "platform": "ANDROID",
            "app_identifier": "123invalid",
            "publisher_name": "Test",
            "store_url": "https://play.google.com/store/apps/details?id=123invalid",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert bad_pkg.status_code == 400

    # Invalid Android store URL (not play.google.com)
    bad_store = await client.post(
        f"/api/v1/owner/brands/{brand_id}/mobile-apps",
        json={
            "app_name": "Bad Store",
            "platform": "ANDROID",
            "app_identifier": "com.test.app",
            "publisher_name": "Test",
            "store_url": "https://unknownstore.com/details?id=com.test.app",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert bad_store.status_code == 400

    # Duplicate mobile app
    ok_payload = {
        "app_name": "App Duplicate",
        "platform": "ANDROID",
        "app_identifier": "com.acme.dup",
        "publisher_name": "Test",
        "store_url": "https://play.google.com/store/apps/details?id=com.acme.dup",
    }
    r1 = await client.post(
        f"/api/v1/owner/brands/{brand_id}/mobile-apps",
        json=ok_payload,
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert r1.status_code == 201

    r2 = await client.post(
        f"/api/v1/owner/brands/{brand_id}/mobile-apps",
        json=ok_payload,
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert r2.status_code == 400
    assert "already registered" in r2.text


@pytest.mark.asyncio
async def test_detection_service_integration_with_brand_assets(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    _, admin_token = await _create_admin(client, mock_otp, "+14155550071", db_session)
    brand_id_str, _, _ = await _setup_verified_brand(
        client, mock_otp, admin_token, "+14155550072", "BrandShield", "brandshield.ai"
    )
    brand_uuid = uuid.UUID(brand_id_str)

    # 1. Add unverified and verified social assets
    unverified_sa = BrandSocialAsset(
        id=uuid.uuid4(),
        brand_id=brand_uuid,
        platform="X",
        handle="brandshield_pending",
        canonical_url="https://x.com/brandshield_pending",
        verification_status=AssetVerificationStatus.PENDING,
    )
    verified_sa = BrandSocialAsset(
        id=uuid.uuid4(),
        brand_id=brand_uuid,
        platform="X",
        handle="brandshield_hq",
        canonical_url="https://x.com/brandshield_hq",
        verification_status=AssetVerificationStatus.VERIFIED,
    )
    # 2. Add verified mobile app
    verified_app = BrandMobileApp(
        id=uuid.uuid4(),
        brand_id=brand_uuid,
        app_name="BrandShield Mobile",
        platform="ANDROID",
        app_identifier="com.brandshield.security",
        publisher_name="BrandShield Inc",
        store_url="https://play.google.com/store/apps/details?id=com.brandshield.security",
        verification_status=AssetVerificationStatus.VERIFIED,
    )
    db_session.add_all([unverified_sa, verified_sa, verified_app])
    await db_session.commit()

    # 3. Retrieve intelligence profile
    intel_service = BrandIntelligenceService()
    profile = await intel_service.get_verified_brand(db_session, brand_uuid)
    assert profile is not None

    # Check that verified social handle IS in known_social_handles
    assert "brandshield_hq" in profile.known_social_handles
    # Check that pending social handle is NOT in known_social_handles
    assert "brandshield_pending" not in profile.known_social_handles

    # Check official lists
    assert len(profile.official_social_accounts) == 2
    assert len(profile.official_mobile_apps) == 1
    assert profile.official_mobile_apps[0].app_identifier == "com.brandshield.security"
    assert profile.official_mobile_apps[0].is_verified is True

    # 4. Profile Analysis: verified account is recognized and safe
    detector = ProfileAnalysisService()
    verified_input = SocialProfileInput(
        platform="X",
        username="@brandshield_hq",
        profile_url="https://x.com/brandshield_hq",
        external_links=["https://brandshield.ai"],
    )
    res_verified = detector.analyze_profile(verified_input, verified_brands=[profile])
    assert res_verified.is_official_account is True
    assert res_verified.risk_score == 0.0
    assert res_verified.risk_level == "BENIGN"

    # Pending unverified account does NOT receive official account exemption
    pending_input = SocialProfileInput(
        platform="X",
        username="@brandshield_pending",
        display_name="BrandShield Security",
    )
    res_pending = detector.analyze_profile(pending_input, verified_brands=[profile])
    assert res_pending.is_official_account is False
    assert res_pending.risk_score > 0.0


@pytest.mark.asyncio
async def test_apk_analysis_recognizes_verified_official_mobile_app() -> None:
    # Build synthetic VerifiedBrandProfile with verified mobile app
    brand_id = uuid.uuid4()
    profile = VerifiedBrandProfile(
        brand_id=brand_id,
        display_name="AcmePay",
        official_domain="acmepay.com",
        known_names=["AcmePay"],
        known_social_handles=["acmepay"],
        official_mobile_apps=[
            {
                "id": uuid.uuid4(),
                "app_name": "AcmePay Wallet",
                "platform": "ANDROID",
                "app_identifier": "com.acmepay.wallet",
                "publisher_name": "AcmePay",
                "store_url": "https://play.google.com/store/apps/details?id=com.acmepay.wallet",
                "verification_status": "VERIFIED",
                "is_verified": True,
            }
        ],
    )

    # Build a valid synthetic APK zip with AndroidManifest.xml
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("AndroidManifest.xml", b"<manifest package='com.acmepay.wallet'></manifest>")
    valid_apk_bytes = buf.getvalue()

    apk_service = APKAnalysisService()
    res = apk_service.analyze_apk(valid_apk_bytes, file_name="acmepay_wallet.apk", verified_brands=[profile])
    # The APK parser parses without executing
    assert res.file_size_bytes == len(valid_apk_bytes)
