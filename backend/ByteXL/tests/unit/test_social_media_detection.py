import pytest
from app.services.detection.social_media_detector import SocialMediaThreatDetector


class TestSocialMediaDetection:
    """Real-world threat detection tests"""

    @pytest.fixture
    def detector(self):
        """Initialize detector without auth (fallback mode)"""
        return SocialMediaThreatDetector(twitter_bearer=None)

    @pytest.mark.asyncio
    async def test_detect_twitter_lookalike_handles(self, detector):
        """Test detection of typosquatted Twitter handles"""
        threats = await detector.detect_twitter_threats(
            brand_name="ApexBank",
            official_handle="apexbank",
        )

        # Should detect impersonation attempts
        assert len(threats) > 0, "Should detect at least one suspicious profile"

        # Top threat should have high similarity to brand name
        top_threat = threats[0]
        assert top_threat.risk_score >= 0.70, f"Risk score should be high, got {top_threat.risk_score}"
        assert "handle_similarity" in top_threat.indicators

    @pytest.mark.asyncio
    async def test_skip_official_verified_account(self, detector):
        """Ensure official verified account is NOT flagged"""
        threats = await detector.detect_twitter_threats(
            brand_name="ApexBank",
            official_handle="apexbank",
        )

        # Official account should NOT appear in threats
        official_found = any(t.handle == "apexbank" for t in threats)
        assert not official_found, "Official account was incorrectly flagged"

    @pytest.mark.asyncio
    async def test_scam_signal_detection_in_bio(self, detector):
        """Test detection of scam language in profile bio"""
        threats = await detector.detect_twitter_threats(
            brand_name="ApexBank"
        )

        # Find profiles with scam signals
        scam_profiles = [t for t in threats if "scam_signals" in t.indicators]
        assert len(scam_profiles) > 0, "Expected scam profile with urgency signals"
        assert scam_profiles[0].risk_score > 0.65, "Scam signal should increase risk"

    @pytest.mark.asyncio
    async def test_account_age_new_suspicious_profile(self, detector):
        """Test that brand-new accounts are flagged"""
        threats = await detector.detect_twitter_threats(
            brand_name="ApexBank"
        )

        # Find brand-new accounts with similar names
        suspicious_new = [
            t for t in threats
            if "account_age_days" in t.indicators and t.indicators["account_age_days"] < 30
        ]

        assert len(suspicious_new) > 0, "Expected recently created profiles"
        for profile in suspicious_new:
            assert profile.risk_score > 0.60, "New suspicious profile should be flagged"

    @pytest.mark.asyncio
    async def test_unverified_imposter_flag(self, detector):
        """Test detection of unverified accounts mimicking official brand"""
        threats = await detector.detect_twitter_threats(
            brand_name="ApexBank",
            official_handle="apexbank",
        )

        imposters = [
            t for t in threats
            if not t.verified and t.risk_score >= 0.70
        ]

        assert len(imposters) > 0, "Expected unverified imposter profiles"
        for imposter in imposters:
            assert (
                "unverified_imposter" in imposter.indicators
                or "handle_similarity" in imposter.indicators
            )
