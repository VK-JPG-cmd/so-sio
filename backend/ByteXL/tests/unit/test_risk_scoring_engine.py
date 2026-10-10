"""
Unit tests for RiskScoringEngine:
- Score boundaries & clamping (0 to 100)
- Category weight caps
- Score reproducibility
- Missing signals (zero points & tracked as unavailable)
- Duplicate indicator deduplication
- Severity mapping thresholds
- Version tracking
- Explanation correctness
- Schema validation
"""

import pytest
from pydantic import ValidationError
from app.models.enums import RiskSeverity
from app.schemas.risk_assessment import RiskAssessmentResponse
from app.services.scoring.config import (
    CATEGORY_WEIGHT_CAPS,
    SCORING_METHODOLOGY_DISCLAIMER,
    SCORING_RULE_VERSION,
)
from app.services.scoring.engine import (
    RiskScoringEngine,
    SignalItem,
    UnavailableSignal,
)


def test_score_boundaries_clamping() -> None:
    """Verify that total risk score is strictly clamped between 0.0 and 100.0."""
    engine = RiskScoringEngine()

    # 1. Zero score lower bound
    res_zero = engine.evaluate_signals(signals=[])
    assert res_zero.risk_score == 0.0
    assert res_zero.severity == RiskSeverity.LOW

    # 2. Score clamping at 100.0 even with massive overflowing signals
    overflowing_signals = [
        SignalItem(category="DOMAIN_SIMILARITY", signal_type="S1", points=100.0, description="D1"),
        SignalItem(category="VISUAL_SIMILARITY", signal_type="S2", points=100.0, description="D2"),
        SignalItem(category="SCAM_AND_CREDENTIAL_HARVESTING", signal_type="S3", points=100.0, description="D3"),
        SignalItem(category="THREAT_INTELLIGENCE", signal_type="S4", points=100.0, description="D4"),
        SignalItem(category="REDIRECT_AND_INFRASTRUCTURE", signal_type="S5", points=100.0, description="D5"),
    ]
    res_overflow = engine.evaluate_signals(signals=overflowing_signals)
    assert res_overflow.risk_score == 100.0
    assert res_overflow.severity == RiskSeverity.CRITICAL


def test_category_weight_caps() -> None:
    """Verify that each category respects its maximum point weight cap."""
    engine = RiskScoringEngine()

    # Domain similarity is capped at 25.0 points
    signals = [
        SignalItem(category="DOMAIN_SIMILARITY", signal_type="T1", points=20.0, description="Sim 1"),
        SignalItem(category="DOMAIN_SIMILARITY", signal_type="T2", points=20.0, description="Sim 2"),
    ]
    res = engine.evaluate_signals(signals=signals)
    assert res.risk_score == CATEGORY_WEIGHT_CAPS["DOMAIN_SIMILARITY"]  # 25.0, not 40.0
    assert res.explanation["score_breakdown"]["DOMAIN_SIMILARITY"]["points_awarded"] == 25.0


def test_score_reproducibility() -> None:
    """Verify that evaluating the exact same signals produces identical results."""
    engine = RiskScoringEngine()

    signals = [
        SignalItem(category="DOMAIN_SIMILARITY", signal_type="HOMO", points=15.0, description="Lookalike"),
        SignalItem(category="THREAT_INTELLIGENCE", signal_type="FEED", points=15.0, description="Feed"),
        SignalItem(category="SCAM_AND_CREDENTIAL_HARVESTING", signal_type="URGENCY", points=5.0, description="Urgent"),
    ]
    unavailable = [
        UnavailableSignal(category="VISUAL_SIMILARITY", reason="No images provided"),
    ]

    res1 = engine.evaluate_signals(signals=signals, unavailable_signals=unavailable)
    res2 = engine.evaluate_signals(signals=signals, unavailable_signals=unavailable)

    assert res1.risk_score == res2.risk_score
    assert res1.severity == res2.severity
    assert res1.explanation == res2.explanation
    assert res1.indicators == res2.indicators
    assert res1.recommendations == res2.recommendations


def test_missing_signals_do_not_penalize() -> None:
    """
    Verify that unavailable signals:
    1. Contribute 0.0 points to the risk score.
    2. Are explicitly listed under 'unavailable_signals'.
    3. Missing data is never interpreted as proof of malicious behavior.
    """
    engine = RiskScoringEngine()

    unavailable = [
        UnavailableSignal(category="VISUAL_SIMILARITY", reason="No logo image uploaded"),
        UnavailableSignal(category="REDIRECT_AND_INFRASTRUCTURE", reason="Offline policy bypassed probing"),
    ]

    res = engine.evaluate_signals(signals=[], unavailable_signals=unavailable)
    assert res.risk_score == 0.0
    assert res.severity == RiskSeverity.LOW

    unavail_json = res.explanation["unavailable_signals"]
    assert len(unavail_json) == 2
    assert unavail_json[0]["category"] == "VISUAL_SIMILARITY"
    assert "Missing data is strictly treated as unavailable" in res.explanation["missing_data_note"]


def test_duplicate_indicators_deduplicated() -> None:
    """Verify duplicate signals of the same category and signal_type are not counted repeatedly."""
    engine = RiskScoringEngine()

    # Three identical homoglyph signals supplied
    duplicate_signals = [
        SignalItem(category="DOMAIN_SIMILARITY", signal_type="HOMOGLYPH_LOOKALIKE", points=15.0, description="Homo 1"),
        SignalItem(category="DOMAIN_SIMILARITY", signal_type="HOMOGLYPH_LOOKALIKE", points=15.0, description="Homo 2"),
        SignalItem(category="DOMAIN_SIMILARITY", signal_type="HOMOGLYPH_LOOKALIKE", points=15.0, description="Homo 3"),
    ]

    res = engine.evaluate_signals(signals=duplicate_signals)
    # Deduplication ensures only 15.0 points awarded, not 45.0
    assert res.risk_score == 15.0
    assert len(res.indicators) == 1


def test_severity_mapping_boundaries() -> None:
    """Verify precise threshold partitioning for LOW, MEDIUM, HIGH, CRITICAL."""
    engine = RiskScoringEngine()

    assert engine.calculate_severity(0.0) == RiskSeverity.LOW
    assert engine.calculate_severity(29.99) == RiskSeverity.LOW
    assert engine.calculate_severity(30.0) == RiskSeverity.MEDIUM
    assert engine.calculate_severity(59.99) == RiskSeverity.MEDIUM
    assert engine.calculate_severity(60.0) == RiskSeverity.HIGH
    assert engine.calculate_severity(79.99) == RiskSeverity.HIGH
    assert engine.calculate_severity(80.0) == RiskSeverity.CRITICAL
    assert engine.calculate_severity(100.0) == RiskSeverity.CRITICAL


def test_version_tracking() -> None:
    """Verify scoring rule version is stamped into every assessment."""
    engine = RiskScoringEngine(rule_version="1.0.0-custom-test")
    res = engine.evaluate_signals(signals=[])
    assert res.model_version == "1.0.0-custom-test"
    assert res.explanation["scoring_rule_version"] == "1.0.0-custom-test"


def test_explanation_correctness_and_disclaimer() -> None:
    """Verify that every contributing signal and category breakdown is transparently explained."""
    engine = RiskScoringEngine()

    signals = [
        SignalItem(category="DOMAIN_SIMILARITY", signal_type="SIM", points=20.0, description="Brand similarity"),
        SignalItem(category="THREAT_INTELLIGENCE", signal_type="FEED", points=15.0, description="Threat intel match"),
    ]
    res = engine.evaluate_signals(signals=signals)

    assert res.explanation["methodology_disclaimer"] == SCORING_METHODOLOGY_DISCLAIMER
    assert res.explanation["score_breakdown"]["DOMAIN_SIMILARITY"]["points_awarded"] == 20.0
    assert res.explanation["score_breakdown"]["THREAT_INTELLIGENCE"]["points_awarded"] == 15.0
    assert "DOMAIN_SIMILARITY" in res.explanation["evaluated_categories"]
    assert "THREAT_INTELLIGENCE" in res.explanation["evaluated_categories"]


def test_invalid_assessment_schema_validation() -> None:
    """Verify Pydantic schema rejects invalid risk scores."""
    import uuid
    from datetime import datetime, timezone

    # Valid schema passes
    valid = RiskAssessmentResponse(
        id=uuid.uuid4(),
        report_id=uuid.uuid4(),
        entity_id="example.com",
        model_version=SCORING_RULE_VERSION,
        risk_score=75.5,
        severity=RiskSeverity.HIGH,
        explanation_json={},
        indicators_json=[],
        recommendation_json=[],
        created_at=datetime.now(timezone.utc),
    )
    assert valid.risk_score == 75.5

    # Out-of-bounds score (< 0) fails validation
    with pytest.raises(ValidationError):
        RiskAssessmentResponse(
            id=uuid.uuid4(),
            report_id=uuid.uuid4(),
            entity_id="example.com",
            model_version=SCORING_RULE_VERSION,
            risk_score=-5.0,
            severity=RiskSeverity.LOW,
            explanation_json={},
            indicators_json=[],
            recommendation_json=[],
            created_at=datetime.now(timezone.utc),
        )

    # Out-of-bounds score (> 100) fails validation
    with pytest.raises(ValidationError):
        RiskAssessmentResponse(
            id=uuid.uuid4(),
            report_id=uuid.uuid4(),
            entity_id="example.com",
            model_version=SCORING_RULE_VERSION,
            risk_score=105.0,
            severity=RiskSeverity.CRITICAL,
            explanation_json={},
            indicators_json=[],
            recommendation_json=[],
            created_at=datetime.now(timezone.utc),
        )
