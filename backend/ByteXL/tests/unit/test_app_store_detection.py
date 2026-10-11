import pytest
from app.services.detection.app_store_detector import AppStoreDetector, AppPlatform


class TestAppStoreDetection:

    @pytest.fixture
    def detector(self):
        return AppStoreDetector()

    @pytest.mark.asyncio
    async def test_detect_google_play_lookalike_apps(self, detector):
        """Test detection of fake banking apps on Google Play"""
        threats = await detector.detect_google_play_threats(
            brand_name="ApexBank",
            official_package_id="com.apexbank.mobile",
        )

        # Should detect suspicious apps
        assert len(threats) > 0, "Should detect at least one suspicious app"

        top_threat = threats[0]
        assert top_threat.risk_score >= 0.65
        assert top_threat.platform == AppPlatform.GOOGLE_PLAY

    @pytest.mark.asyncio
    async def test_skip_official_app(self, detector):
        """Ensure official app is not flagged"""
        threats = await detector.detect_google_play_threats(
            brand_name="ApexBank",
            official_package_id="com.apexbank.mobile",
        )

        # Official app should NOT appear
        official_found = any(
            t.package_id == "com.apexbank.mobile" for t in threats
        )
        assert not official_found, "Official app was incorrectly flagged"

    @pytest.mark.asyncio
    async def test_detect_dangerous_permissions(self, detector):
        """Test detection of high-risk permissions"""
        threats = await detector.detect_google_play_threats(
            brand_name="ApexBank"
        )

        dangerous_perm_apps = [
            t for t in threats
            if "dangerous_permissions" in t.indicators
        ]

        assert len(dangerous_perm_apps) > 0, "Expected apps with dangerous permissions"
        assert dangerous_perm_apps[0].risk_score > 0.65

    @pytest.mark.asyncio
    async def test_detect_apple_app_store_lookalikes(self, detector):
        """Test iOS app store threat detection"""
        threats = await detector.detect_apple_app_store_threats(
            brand_name="ApexBank",
            official_bundle_id="com.apexbank.ios",
        )

        assert len(threats) > 0
        assert all(t.platform == AppPlatform.APPLE_APP_STORE for t in threats)

    @pytest.mark.asyncio
    async def test_package_name_homoglyph_detection(self, detector):
        """Test detection of homoglyph package names"""
        threats = await detector.detect_google_play_threats(
            brand_name="ApexBank"
        )

        suspicious = [
            t for t in threats
            if t.indicators.get("package_similarity", 0) > 0.65
        ]

        assert len(suspicious) > 0
        assert suspicious[0].risk_score >= 0.65
