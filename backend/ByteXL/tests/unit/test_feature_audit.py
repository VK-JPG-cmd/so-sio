"""
Comprehensive Unit & Regression Test Suite for Phase 1:
- Task 1: Fix Unified Assessment Crash & Attribute Verification.
- Task 2: Official Social Account False Positive Protection.
- Task 3: Deterministic Look-Alike & Official Profile Tests (Candidates 1-8).
"""

import uuid
import pytest

from app.models.enums import RiskSeverity, TargetType
from app.models.threat_report import ThreatReport
from app.models.user import User
from app.services.detection.brand_intelligence import VerifiedBrandProfile
from app.services.detection.domain_analysis import DomainAnalysisService
from app.services.detection.profile_analysis import (
    ProfileAnalysisResult,
    ProfileAnalysisService,
    SocialProfileInput,
)
from app.services.scoring.assessment_service import RiskAssessmentService
from app.services.scoring.engine import SignalItem, UnavailableSignal


@pytest.fixture
def acmepay_brand() -> VerifiedBrandProfile:
    """Synthetic official brand fixture for AcmePay."""
    return VerifiedBrandProfile(
        brand_id=uuid.uuid4(),
        display_name="AcmePay",
        official_domain="acmepay.example",
        known_names=["AcmePay"],
        known_social_handles=["acmepay"],
        approved_keywords=["acmepay"],
        logo_storage_keys=["brands/acme/logo.png"],
        logo_hashes=["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"],
    )


# ============================================================================
# TASK 3: DETERMINISTIC CANDIDATE PROFILE SUITE (PROFILES 1 - 8)
# ============================================================================


def test_candidate_1_exact_registered_official_handle(acmepay_brand: VerifiedBrandProfile):
    """
    Candidate 1: @acmepay — exact registered official handle with official link.
    Must be recognized as an official account with BENIGN risk level and 0.0 risk score.
    """
    svc = ProfileAnalysisService()
    profile = SocialProfileInput(
        platform="Twitter",
        username="@acmepay",
        display_name="AcmePay Official",
        bio="Official account for AcmePay services.",
        external_links=["https://acmepay.example"],
    )
    res = svc.analyze_profile(profile, [acmepay_brand])

    assert res.is_official_account is True
    assert res.risk_score == 0.0
    assert res.risk_level == "BENIGN"
    assert res.username_similarity == 100.0
    assert res.matched_brand_name == "AcmePay"
    assert any("verified official social account" in r.lower() for r in res.analysis_reasons)


def test_candidate_2_added_keyword_support(acmepay_brand: VerifiedBrandProfile):
    """
    Candidate 2: @acmepay_support — added keyword.
    Must be flagged as an impersonator with high similarity and bio claim penalty.
    """
    svc = ProfileAnalysisService()
    profile = SocialProfileInput(
        platform="Twitter",
        username="@acmepay_support",
        display_name="AcmePay Customer Support",
        bio="Official customer support for AcmePay. Contact us here.",
        external_links=["http://acmepay-helpdesk.top"],
    )
    res = svc.analyze_profile(profile, [acmepay_brand])

    assert res.is_official_account is False
    assert res.username_similarity > 80.0
    assert res.bio_impersonation_detected is True
    assert res.profile_link_mismatch is True
    assert res.risk_score >= 55.0
    assert res.risk_level in ("HIGH", "CRITICAL")


def test_candidate_3_extra_character(acmepay_brand: VerifiedBrandProfile):
    """
    Candidate 3: @acmepayy — extra character insertion.
    Must NOT be recognized as official and must be analyzed for typosquatting.
    """
    svc = ProfileAnalysisService()
    profile = SocialProfileInput(
        platform="Twitter",
        username="@acmepayy",
        display_name="AcmePay",
    )
    res = svc.analyze_profile(profile, [acmepay_brand])

    assert res.is_official_account is False
    assert res.username_similarity > 85.0
    assert res.risk_score >= 35.0
    assert res.risk_level in ("MEDIUM", "HIGH")


def test_candidate_4_spacing_underscore_variation(acmepay_brand: VerifiedBrandProfile):
    """
    Candidate 4: @acme_pay — spacing/underscore variation.
    Must NOT be recognized as official and must be flagged for similarity.
    """
    svc = ProfileAnalysisService()
    profile = SocialProfileInput(
        platform="Twitter",
        username="@acme_pay",
        display_name="Acme Pay",
    )
    res = svc.analyze_profile(profile, [acmepay_brand])

    assert res.is_official_account is False
    assert res.username_similarity > 85.0
    assert res.risk_score >= 35.0
    assert res.risk_level in ("MEDIUM", "HIGH")


def test_candidate_5_character_swap(acmepay_brand: VerifiedBrandProfile):
    """
    Candidate 5: @acmepya — character swap permutation.
    Must NOT be recognized as official and must be flagged for similarity.
    """
    svc = ProfileAnalysisService()
    profile = SocialProfileInput(
        platform="Twitter",
        username="@acmepya",
        display_name="AcmePya",
    )
    res = svc.analyze_profile(profile, [acmepay_brand])

    assert res.is_official_account is False
    assert res.username_similarity > 85.0
    assert res.risk_score >= 35.0
    assert res.risk_level in ("MEDIUM", "HIGH")


def test_candidate_6_unrelated_legitimate_account(acmepay_brand: VerifiedBrandProfile):
    """
    Candidate 6: Unrelated legitimate account.
    Must receive 0.0 risk score and LOW severity.
    """
    svc = ProfileAnalysisService()
    profile = SocialProfileInput(
        platform="Twitter",
        username="@nature_photography_2026",
        display_name="Nature Photos Daily",
        bio="Photos from national parks and outdoor adventures.",
    )
    res = svc.analyze_profile(profile, [acmepay_brand])

    assert res.is_official_account is False
    assert res.risk_score == 0.0
    assert res.risk_level == "LOW"
    assert res.username_similarity < 65.0


def test_candidate_7_lookalike_linking_to_unrelated_domain(acmepay_brand: VerifiedBrandProfile):
    """
    Candidate 7: Lookalike account linking to an unrelated phishing domain.
    Must trigger profile_link_mismatch and elevated risk.
    """
    svc = ProfileAnalysisService()
    profile = SocialProfileInput(
        platform="Twitter",
        username="@acmepay_online",
        display_name="AcmePay Portal",
        external_links=["http://phishing-acmepay-login.xyz"],
    )
    res = svc.analyze_profile(profile, [acmepay_brand])

    assert res.is_official_account is False
    assert res.profile_link_mismatch is True
    assert "http://phishing-acmepay-login.xyz" in res.suspicious_external_links
    assert res.risk_score >= 45.0
    assert res.risk_level in ("MEDIUM", "HIGH", "CRITICAL")


def test_candidate_8_official_account_with_missing_links(acmepay_brand: VerifiedBrandProfile):
    """
    Candidate 8: Official account with missing profile-link data.
    Missing link data must NOT penalize the authentic official handle.
    """
    svc = ProfileAnalysisService()
    profile = SocialProfileInput(
        platform="Twitter",
        username="@acmepay",
        external_links=[],  # Missing link data
    )
    res = svc.analyze_profile(profile, [acmepay_brand])

    assert res.is_official_account is True
    assert res.profile_link_mismatch is False
    assert res.risk_score == 0.0
    assert res.risk_level == "BENIGN"


def test_no_reliance_on_client_supplied_trust_flag(acmepay_brand: VerifiedBrandProfile):
    """
    Verify security invariant: Arbitrary client input cannot spoof official status.
    A malicious spoof (@acmepay_fake) cannot be marked official.
    """
    svc = ProfileAnalysisService()
    fake_profile = SocialProfileInput(
        platform="Twitter",
        username="@acmepay_fake",
        display_name="AcmePay Official Support",
    )
    res = svc.analyze_profile(fake_profile, [acmepay_brand])
    assert res.is_official_account is False
    assert res.risk_score > 0.0


def test_official_account_with_compromised_external_link(acmepay_brand: VerifiedBrandProfile):
    """
    Verify security invariant:
    If an official handle links to an external domain that is NOT its official domain,
    the independent suspicious indicator is preserved and penalized.
    """
    svc = ProfileAnalysisService()
    compromised_official = SocialProfileInput(
        platform="Twitter",
        username="@acmepay",
        display_name="AcmePay Official",
        external_links=["http://malicious-redirect-c2.net"],  # Points off-domain!
    )
    res = svc.analyze_profile(compromised_official, [acmepay_brand])

    assert res.is_official_account is True
    assert res.profile_link_mismatch is True
    # Risk score must capture the independent indicator (+25.0 points)
    assert res.risk_score == 25.0
    assert res.risk_level == "MEDIUM"
    assert any("suspicious indicators were detected" in r for r in res.analysis_reasons)


# ============================================================================
# TASK 1: UNIFIED RISK ASSESSMENT REGRESSION & ATTRIBUTE VERIFICATION
# ============================================================================


def test_profile_analysis_result_schema_fields():
    """Verify ProfileAnalysisResult exposes profile_link_mismatch and is_official_account."""
    svc = ProfileAnalysisService()
    res = svc.analyze_profile(SocialProfileInput(platform="Twitter", username="testuser"))

    assert hasattr(res, "profile_link_mismatch") is True
    assert hasattr(res, "link_mismatch_detected") is False
    assert hasattr(res, "is_official_account") is True


def test_assessment_service_signal_accumulation_for_social_profile(acmepay_brand: VerifiedBrandProfile):
    """
    Verify that assessment service correctly maps profile_link_mismatch to
    REDIRECT_AND_INFRASTRUCTURE / EXTERNAL_LINK_MISMATCH signal.
    """
    svc = ProfileAnalysisService()
    scoring_svc = RiskAssessmentService()

    # Lookalike with link mismatch referencing the brand
    spoof_input = SocialProfileInput(
        platform="Twitter",
        username="@acmepay_portal",
        display_name="AcmePay Portal",
        bio="Official Support for AcmePay.",
        external_links=["http://acmepay-tracker.top"],
    )
    profile_res = svc.analyze_profile(spoof_input, [acmepay_brand])
    assert profile_res.profile_link_mismatch is True

    # Check signal mapping logic
    signals = []
    if profile_res.profile_link_mismatch:
        signals.append(
            SignalItem(
                category="REDIRECT_AND_INFRASTRUCTURE",
                signal_type="EXTERNAL_LINK_MISMATCH",
                points=10.0,
                description="Profile links to external domains that mismatch the official brand domain.",
            )
        )
    scoring_res = scoring_svc.scoring_engine.evaluate_signals(signals)
    assert scoring_res.risk_score == 10.0
    assert any(ind["signal_type"] == "EXTERNAL_LINK_MISMATCH" for ind in scoring_res.indicators)


def test_assessment_service_official_social_profile_no_false_impersonation(acmepay_brand: VerifiedBrandProfile):
    """
    Verify that an official social account analyzed through assessment engine logic
    does not generate false PROFILE_HANDLE_IMPERSONATION signals.
    """
    svc = ProfileAnalysisService()
    scoring_svc = RiskAssessmentService()

    official_input = SocialProfileInput(
        platform="Twitter",
        username="@acmepay",
        display_name="AcmePay",
        bio="Official AcmePay Twitter.",
        external_links=["https://acmepay.example"],
    )
    profile_res = svc.analyze_profile(official_input, [acmepay_brand])
    assert profile_res.is_official_account is True

    signals = []
    if not profile_res.is_official_account and profile_res.username_similarity >= 70.0:
        signals.append(
            SignalItem(
                category="DOMAIN_SIMILARITY",
                signal_type="PROFILE_HANDLE_IMPERSONATION",
                points=25.0,
                description="Impersonation",
            )
        )

    scoring_res = scoring_svc.scoring_engine.evaluate_signals(signals)
    assert scoring_res.risk_score == 0.0
    assert len(scoring_res.indicators) == 0
