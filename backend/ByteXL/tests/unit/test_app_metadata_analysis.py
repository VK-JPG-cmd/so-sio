from typing import Tuple
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.enums import AssetVerificationStatus, RiskSeverity, UserRole
from app.models.official_mobile_asset import BrandMobileApp
from app.models.user import User
from app.schemas.app_metadata import AppMetadataAnalysisRequest
from app.services.detection.app_metadata_analysis import AppMetadataAnalysisService
from app.services.detection.brand_intelligence import BrandIntelligenceService
from app.services.otp_provider import MockOTPProvider


async def _create_user(client: AsyncClient, mock_otp: MockOTPProvider, phone: str) -> Tuple[str, str]:
    await client.post("/api/v1/auth/otp/start", json={"phone_number": phone})
    code = mock_otp.get_last_code(phone)
    verify_res = await client.post(
        "/api/v1/auth/otp/verify", json={"phone_number": phone, "code": code}
    )
    data = verify_res.json()
    return data["user"]["id"], data["access_token"]


async def _create_admin(
    client: AsyncClient, mock_otp: MockOTPProvider, phone: str, db_session: AsyncSession
) -> Tuple[str, str]:
    user_id, token = await _create_user(client, mock_otp, phone)
    await db_session.execute(
        update(User).where(User.id == uuid.UUID(user_id)).values(role=UserRole.ADMIN)
    )
    await db_session.commit()
    return user_id, token


async def _setup_acmepay_fixture(
    client: AsyncClient, mock_otp: MockOTPProvider, admin_token: str, phone: str
) -> Tuple[str, str, str]:
    """Sets up AcmePay brand with registered official application AcmePay Wallet."""
    owner_id, owner_token = await _create_user(client, mock_otp, phone)
    app_res = await client.post(
        "/api/v1/brand-applications",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"business_name": "AcmePay", "official_domain": "acmepay.com"},
    )
    app_id = app_res.json()["id"]

    review_res = await client.post(
        f"/api/v1/admin/brand-applications/{app_id}/review",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"decision": "APPROVE", "notes": "Approved AcmePay"},
    )
    brand_id = str(review_res.json()["brand_id"])

    # Register official mobile app
    create_app_res = await client.post(
        f"/api/v1/owner/brands/{brand_id}/mobile-apps",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "app_name": "AcmePay Wallet",
            "platform": "ANDROID",
            "app_identifier": "com.acmepay.wallet",
            "publisher_name": "AcmePay Technologies",
            "store_url": "https://play.google.com/store/apps/details?id=com.acmepay.wallet",
        },
    )
    mobile_app_id = create_app_res.json()["id"]

    # Verify official app as admin
    await client.patch(
        f"/api/v1/owner/brands/{brand_id}/mobile-apps/{mobile_app_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"verification_status": "VERIFIED"},
    )

    return brand_id, owner_id, owner_token


# =============================================================================
# 1. Exact Registered Official Application
# =============================================================================
@pytest.mark.asyncio
async def test_case_01_and_17_exact_registered_official_app(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    _, admin_token = await _create_admin(client, mock_otp, "+14155551001", db_session)
    brand_id, _, owner_token = await _setup_acmepay_fixture(client, mock_otp, admin_token, "+14155551002")

    res = await client.post(
        "/api/v1/analyze/app-metadata",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "brand_id": brand_id,
            "app_name": "AcmePay Wallet",
            "platform": "ANDROID",
            "app_identifier": "com.acmepay.wallet",
            "publisher_name": "AcmePay Technologies",
            "store_url": "https://play.google.com/store/apps/details?id=com.acmepay.wallet",
            "description": "Official mobile wallet from AcmePay Technologies.",
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["is_official_match"] is True
    assert data["assessment_status"] == "OFFICIAL_ASSET_MATCH"
    assert data["risk_score"] == 0.0
    assert data["severity"] == "LOW"
    assert len(data["contributing_indicators"]) == 0
    assert "matches verified official mobile application" in data["explanations"][0]


# =============================================================================
# 2. Similar Application Name with Different Package Identifier
# =============================================================================
@pytest.mark.asyncio
async def test_case_02_similar_app_name_different_package(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    _, admin_token = await _create_admin(client, mock_otp, "+14155551011", db_session)
    brand_id, _, owner_token = await _setup_acmepay_fixture(client, mock_otp, admin_token, "+14155551012")

    res = await client.post(
        "/api/v1/analyze/app-metadata",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "brand_id": brand_id,
            "app_name": "AcmePay Fast Wallet",
            "platform": "ANDROID",
            "app_identifier": "com.rogue.quickpay",
            "publisher_name": "Rogue Developer",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_official_match"] is False
    assert data["risk_score"] > 0.0
    signals = [i["signal_type"] for i in data["contributing_indicators"]]
    assert "APP_NAME_IMPERSONATION" in signals or "KEYWORD_IN_APP_NAME" in signals
    assert data["assessment_status"] in ("NEEDS_INVESTIGATION", "LIKELY_IMPERSONATION")


# =============================================================================
# 3. Added Keyword (AcmePay Secure Wallet)
# =============================================================================
@pytest.mark.asyncio
async def test_case_03_added_keyword_acmepay_secure_wallet(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    _, admin_token = await _create_admin(client, mock_otp, "+14155551021", db_session)
    brand_id, _, owner_token = await _setup_acmepay_fixture(client, mock_otp, admin_token, "+14155551022")

    res = await client.post(
        "/api/v1/analyze/app-metadata",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "brand_id": brand_id,
            "app_name": "AcmePay Secure Wallet",
            "platform": "ANDROID",
            "app_identifier": "com.different.app",
        },
    )
    assert res.status_code == 200
    data = res.json()
    signals = [i["signal_type"] for i in data["contributing_indicators"]]
    assert "KEYWORD_IN_APP_NAME" in signals


# =============================================================================
# 4. Similar Package Identifier
# =============================================================================
@pytest.mark.asyncio
async def test_case_04_similar_package_identifier(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    _, admin_token = await _create_admin(client, mock_otp, "+14155551031", db_session)
    brand_id, _, owner_token = await _setup_acmepay_fixture(client, mock_otp, admin_token, "+14155551032")

    res = await client.post(
        "/api/v1/analyze/app-metadata",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "brand_id": brand_id,
            "app_name": "Finance Tool",
            "platform": "ANDROID",
            "app_identifier": "com.acmepay.wallet.clone",
        },
    )
    assert res.status_code == 200
    data = res.json()
    signals = [i["signal_type"] for i in data["contributing_indicators"]]
    assert "SIMILAR_PACKAGE_IDENTIFIER" in signals


# =============================================================================
# 5. Different Publisher Name
# =============================================================================
@pytest.mark.asyncio
async def test_case_05_different_publisher_name(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    _, admin_token = await _create_admin(client, mock_otp, "+14155551041", db_session)
    brand_id, _, owner_token = await _setup_acmepay_fixture(client, mock_otp, admin_token, "+14155551042")

    res = await client.post(
        "/api/v1/analyze/app-metadata",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "brand_id": brand_id,
            "app_name": "AcmePay Wallet",
            "platform": "ANDROID",
            "app_identifier": "com.acmepay.wallet",
            "publisher_name": "Fraudulent Publisher LLC",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_official_match"] is False
    signals = [i["signal_type"] for i in data["contributing_indicators"]]
    assert "PUBLISHER_MISMATCH" in signals or "PACKAGE_IDENTIFIER_UNVERIFIED_LISTING" in signals


# =============================================================================
# 6. Description Claiming to Represent AcmePay
# =============================================================================
@pytest.mark.asyncio
async def test_case_06_description_claims_official_representation(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    _, admin_token = await _create_admin(client, mock_otp, "+14155551051", db_session)
    brand_id, _, owner_token = await _setup_acmepay_fixture(client, mock_otp, admin_token, "+14155551052")

    res = await client.post(
        "/api/v1/analyze/app-metadata",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "brand_id": brand_id,
            "app_name": "Helper App",
            "platform": "ANDROID",
            "app_identifier": "com.helper.app",
            "description": "This is the official support app for AcmePay customers.",
        },
    )
    assert res.status_code == 200
    data = res.json()
    signals = [i["signal_type"] for i in data["contributing_indicators"]]
    assert "DESCRIPTION_IMPERSONATION_CLAIM" in signals


# =============================================================================
# 7. Suspicious Credential-Harvesting Description
# =============================================================================
@pytest.mark.asyncio
async def test_case_07_suspicious_credential_harvesting_description(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    _, admin_token = await _create_admin(client, mock_otp, "+14155551061", db_session)
    brand_id, _, owner_token = await _setup_acmepay_fixture(client, mock_otp, admin_token, "+14155551062")

    res = await client.post(
        "/api/v1/analyze/app-metadata",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "brand_id": brand_id,
            "app_name": "Fast Helper",
            "platform": "ANDROID",
            "app_identifier": "com.helper.fast",
            "description": "Please enter your password and recovery seed phrase to unlock bonus payment rewards.",
        },
    )
    assert res.status_code == 200
    data = res.json()
    signals = [i["signal_type"] for i in data["contributing_indicators"]]
    assert "CREDENTIAL_HARVESTING_LURE" in signals
    assert data["risk_score"] >= 25.0


# =============================================================================
# 8. Unrelated Legitimate Application
# =============================================================================
@pytest.mark.asyncio
async def test_case_08_unrelated_legitimate_application(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    _, admin_token = await _create_admin(client, mock_otp, "+14155551071", db_session)
    brand_id, _, owner_token = await _setup_acmepay_fixture(client, mock_otp, admin_token, "+14155551072")

    res = await client.post(
        "/api/v1/analyze/app-metadata",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "brand_id": brand_id,
            "app_name": "Zen Meditation Timer",
            "platform": "ANDROID",
            "app_identifier": "com.mindfulness.zentimer",
            "publisher_name": "Zen Studios",
            "description": "Calm relaxing sounds and countdown meditation timer.",
            "store_url": "https://play.google.com/store/apps/details?id=com.mindfulness.zentimer",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_official_match"] is False
    assert data["risk_score"] == 0.0
    assert data["assessment_status"] == "BENIGN_UNRELATED"
    assert data["severity"] == "LOW"


# =============================================================================
# 9 & 10. Missing Publisher and Description Handled as Missing Signals
# =============================================================================
@pytest.mark.asyncio
async def test_case_09_and_10_missing_optional_fields_not_penalized(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    _, admin_token = await _create_admin(client, mock_otp, "+14155551081", db_session)
    brand_id, _, owner_token = await _setup_acmepay_fixture(client, mock_otp, admin_token, "+14155551082")

    res = await client.post(
        "/api/v1/analyze/app-metadata",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "brand_id": brand_id,
            "app_name": "Garden Planner",
            "platform": "ANDROID",
            "app_identifier": "com.plants.garden",
            # publisher_name, description, store_url omitted
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["risk_score"] == 0.0
    missing_cats = [m["category"] for m in data["missing_signals"]]
    assert "SCAM_AND_CREDENTIAL_HARVESTING" in missing_cats
    assert "REDIRECT_AND_INFRASTRUCTURE" in missing_cats
    assert "VISUAL_SIMILARITY" in missing_cats


# =============================================================================
# 11. Invalid Android Package Identifier
# =============================================================================
@pytest.mark.asyncio
async def test_case_11_invalid_android_package_identifier(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    _, admin_token = await _create_admin(client, mock_otp, "+14155551091", db_session)
    brand_id, _, owner_token = await _setup_acmepay_fixture(client, mock_otp, admin_token, "+14155551092")

    res = await client.post(
        "/api/v1/analyze/app-metadata",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "brand_id": brand_id,
            "app_name": "Test App",
            "platform": "ANDROID",
            "app_identifier": "invalid_package_no_dots",
        },
    )
    assert res.status_code == 400
    assert "Invalid Android package name" in res.text


# =============================================================================
# 12. iOS Application with Valid Platform-Specific Identifier
# =============================================================================
@pytest.mark.asyncio
async def test_case_12_ios_application_valid_identifier(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    _, admin_token = await _create_admin(client, mock_otp, "+14155551101", db_session)
    brand_id, _, owner_token = await _setup_acmepay_fixture(client, mock_otp, admin_token, "+14155551102")

    res = await client.post(
        "/api/v1/analyze/app-metadata",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "brand_id": brand_id,
            "app_name": "Recipe Finder",
            "platform": "IOS",
            "app_identifier": "id1234567890",
            "store_url": "https://apps.apple.com/app/recipe-finder/id1234567890",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["platform"] == "IOS"
    assert data["app_identifier"] == "id1234567890"
    assert data["risk_score"] == 0.0


# =============================================================================
# 13. Invalid Store URL
# =============================================================================
@pytest.mark.asyncio
async def test_case_13_invalid_store_url(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    _, admin_token = await _create_admin(client, mock_otp, "+14155551111", db_session)
    brand_id, _, owner_token = await _setup_acmepay_fixture(client, mock_otp, admin_token, "+14155551112")

    res = await client.post(
        "/api/v1/analyze/app-metadata",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "brand_id": brand_id,
            "app_name": "Test App",
            "platform": "ANDROID",
            "app_identifier": "com.test.app",
            "store_url": "ftp://not-http-url",
        },
    )
    assert res.status_code == 400


# =============================================================================
# 14. Store URL Whose Host Does Not Match Declared Platform
# =============================================================================
@pytest.mark.asyncio
async def test_case_14_store_url_host_mismatch_flagged(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    _, admin_token = await _create_admin(client, mock_otp, "+14155551121", db_session)
    brand_id, _, owner_token = await _setup_acmepay_fixture(client, mock_otp, admin_token, "+14155551122")

    res = await client.post(
        "/api/v1/analyze/app-metadata",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "brand_id": brand_id,
            "app_name": "Test App",
            "platform": "ANDROID",
            "app_identifier": "com.test.app",
            "store_url": "https://malicious-apk-host.com/download/app",
        },
    )
    assert res.status_code == 200
    data = res.json()
    signals = [i["signal_type"] for i in data["contributing_indicators"]]
    assert "STORE_URL_HOST_MISMATCH" in signals


# =============================================================================
# 15. Unknown Brand ID Returns 404
# =============================================================================
@pytest.mark.asyncio
async def test_case_15_unknown_brand_id(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    _, token = await _create_user(client, mock_otp, "+14155551131")
    fake_id = uuid.uuid4()

    res = await client.post(
        "/api/v1/analyze/app-metadata",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "brand_id": str(fake_id),
            "app_name": "Test App",
            "platform": "ANDROID",
            "app_identifier": "com.test.app",
        },
    )
    assert res.status_code == 404
    assert "not found" in res.text


# =============================================================================
# 16. Unauthorized Access
# =============================================================================
@pytest.mark.asyncio
async def test_case_16_unauthorized_access(client: AsyncClient) -> None:
    res = await client.post(
        "/api/v1/analyze/app-metadata",
        json={
            "brand_id": str(uuid.uuid4()),
            "app_name": "Test App",
            "platform": "ANDROID",
            "app_identifier": "com.test.app",
        },
    )
    assert res.status_code == 401


# =============================================================================
# 18. Risk Score Boundary and Severity Consistency
# =============================================================================
@pytest.mark.asyncio
async def test_case_18_score_boundary_and_severity_consistency(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    _, admin_token = await _create_admin(client, mock_otp, "+14155551141", db_session)
    brand_id, _, owner_token = await _setup_acmepay_fixture(client, mock_otp, admin_token, "+14155551142")

    # High severity candidate
    res = await client.post(
        "/api/v1/analyze/app-metadata",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "brand_id": brand_id,
            "app_name": "AcmePay Wallet Pro",
            "platform": "ANDROID",
            "app_identifier": "com.acmepay.wallet.fake",
            "publisher_name": "Fake Publisher",
            "description": "Official support app! Enter your password and private key immediately.",
            "store_url": "https://third-party-store.com/app",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert 0.0 <= data["risk_score"] <= 100.0
    if data["risk_score"] >= 80.0:
        assert data["severity"] == "CRITICAL"
    elif data["risk_score"] >= 60.0:
        assert data["severity"] == "HIGH"


# =============================================================================
# 19. Duplicate Indicators Not Counted Twice
# =============================================================================
@pytest.mark.asyncio
async def test_case_19_duplicate_indicators_deduplicated(
    db_session: AsyncSession,
) -> None:
    service = AppMetadataAnalysisService()
    # Direct test of scoring engine signal deduplication
    from app.services.scoring.engine import SignalItem
    signals = [
        SignalItem(category="DOMAIN_SIMILARITY", signal_type="APP_NAME_IMPERSONATION", points=20.0, description="Test 1"),
        SignalItem(category="DOMAIN_SIMILARITY", signal_type="APP_NAME_IMPERSONATION", points=20.0, description="Test 2"),
    ]
    scoring = service.scoring_engine.evaluate_signals(signals)
    # Deduplication ensures points are counted only once (20.0, not 40.0)
    assert scoring.risk_score == 20.0
    assert len(scoring.indicators) == 1


# =============================================================================
# 20. Missing Signals Reported Correctly
# =============================================================================
@pytest.mark.asyncio
async def test_case_20_missing_signals_reported_correctly(
    client: AsyncClient, mock_otp: MockOTPProvider, db_session: AsyncSession
) -> None:
    _, admin_token = await _create_admin(client, mock_otp, "+14155551151", db_session)
    brand_id, _, owner_token = await _setup_acmepay_fixture(client, mock_otp, admin_token, "+14155551152")

    res = await client.post(
        "/api/v1/analyze/app-metadata",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "brand_id": brand_id,
            "app_name": "Weather App",
            "platform": "ANDROID",
            "app_identifier": "com.weather.daily",
        },
    )
    assert res.status_code == 200
    data = res.json()
    missing_keys = {m["category"] for m in data["missing_signals"]}
    assert "VISUAL_SIMILARITY" in missing_keys
    assert "REDIRECT_AND_INFRASTRUCTURE" in missing_keys
    assert "SCAM_AND_CREDENTIAL_HARVESTING" in missing_keys
