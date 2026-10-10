"""
Explainable Risk Scoring Engine for BrandShield AI.
Calculates deterministic risk scores (0-100), applies category weight caps,
prevents duplicate indicator counting, records evaluated vs unavailable signals,
and synthesizes actionable recommendations.
"""

from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import RiskSeverity
from app.services.scoring.config import (
    CATEGORY_WEIGHT_CAPS,
    SCORING_METHODOLOGY_DISCLAIMER,
    SCORING_RULE_VERSION,
    SEVERITY_THRESHOLDS,
    STANDARD_RECOMMENDATIONS,
)


class SignalItem(BaseModel):
    """Atomic threat indicator contributing to risk score."""

    category: str  # Must match a key in CATEGORY_WEIGHT_CAPS
    signal_type: str  # e.g., "HOMOGLYPH_UNICODE", "HIGH_DOMAIN_SIMILARITY"
    points: float = Field(..., ge=0.0)
    description: str
    evidence_context: Dict[str, Any] = Field(default_factory=dict)


class UnavailableSignal(BaseModel):
    """Signal category that could not be evaluated due to missing input or offline policy."""

    category: str
    reason: str


class RiskScoringResult(BaseModel):
    """Complete evaluation result output by RiskScoringEngine."""

    model_config = ConfigDict(protected_namespaces=())

    risk_score: float = Field(..., ge=0.0, le=100.0)
    severity: RiskSeverity
    model_version: str
    confidence: Optional[float] = None
    indicators: List[Dict[str, Any]]
    explanation: Dict[str, Any]
    recommendations: List[Dict[str, Any]]


class RiskScoringEngine:
    """
    Core risk calculation engine.
    Ensures explainability, signal deduplication, and bound clamping.
    """

    def __init__(self, rule_version: str = SCORING_RULE_VERSION) -> None:
        self.rule_version = rule_version
        self.category_caps = dict(CATEGORY_WEIGHT_CAPS)

    def calculate_severity(self, score: float) -> RiskSeverity:
        """Map numerical score (0-100) to standard severity tiers."""
        if score >= SEVERITY_THRESHOLDS[RiskSeverity.CRITICAL]:
            return RiskSeverity.CRITICAL
        if score >= SEVERITY_THRESHOLDS[RiskSeverity.HIGH]:
            return RiskSeverity.HIGH
        if score >= SEVERITY_THRESHOLDS[RiskSeverity.MEDIUM]:
            return RiskSeverity.MEDIUM
        return RiskSeverity.LOW

    def evaluate_signals(
        self,
        signals: List[SignalItem],
        unavailable_signals: Optional[List[UnavailableSignal]] = None,
        confidence: Optional[float] = None,
    ) -> RiskScoringResult:
        """
        Evaluate candidate signals into a unified, explainable risk score.
        Deduplicates identical signals within categories and applies category caps.
        """
        unavailable_list = unavailable_signals or []

        # 1. Deduplicate signals by (category, signal_type)
        # Prevents duplicate indicators from being counted repeatedly without justification
        deduplicated_signals: List[SignalItem] = []
        seen_keys: Set[str] = set()

        for sig in signals:
            dedup_key = f"{sig.category}:{sig.signal_type}"
            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)
            deduplicated_signals.append(sig)

        # 2. Accumulate points per category with caps
        category_points: Dict[str, float] = {cat: 0.0 for cat in self.category_caps}
        category_signal_counts: Dict[str, int] = {cat: 0 for cat in self.category_caps}

        for sig in deduplicated_signals:
            cat = sig.category
            if cat in category_points:
                category_points[cat] += sig.points
                category_signal_counts[cat] += 1
            else:
                # Fallback if custom category specified
                category_points[cat] = category_points.get(cat, 0.0) + sig.points
                category_signal_counts[cat] = category_signal_counts.get(cat, 0) + 1

        # Apply category caps
        capped_category_points: Dict[str, float] = {}
        for cat, raw_pts in category_points.items():
            cap = self.category_caps.get(cat, 25.0)
            capped_category_points[cat] = min(round(raw_pts, 2), cap)

        # 3. Sum overall score and clamp between 0.0 and 100.0
        raw_total = sum(capped_category_points.values())
        final_score = max(0.0, min(100.0, round(raw_total, 2)))

        severity = self.calculate_severity(final_score)

        # 4. Build explainability breakdown
        evaluated_categories = [
            cat for cat, count in category_signal_counts.items() if count > 0
        ]
        unavailable_categories = [u.category for u in unavailable_list]

        score_breakdown = {}
        for cat, cap in self.category_caps.items():
            score_breakdown[cat] = {
                "points_awarded": capped_category_points.get(cat, 0.0),
                "max_category_points": cap,
                "signal_count": category_signal_counts.get(cat, 0),
                "is_evaluated": cat in evaluated_categories,
                "is_unavailable": cat in unavailable_categories,
            }

        contributing_indicators = [
            {
                "category": s.category,
                "signal_type": s.signal_type,
                "points": s.points,
                "description": s.description,
                "evidence_context": s.evidence_context,
            }
            for s in deduplicated_signals
        ]

        unavailable_indicators = [
            {"category": u.category, "reason": u.reason}
            for u in unavailable_list
        ]

        explanation = {
            "scoring_rule_version": self.rule_version,
            "final_score": final_score,
            "severity": severity.value,
            "score_breakdown": score_breakdown,
            "contributing_signals_count": len(deduplicated_signals),
            "evaluated_categories": evaluated_categories,
            "unavailable_signals": unavailable_indicators,
            "missing_data_note": "Missing data is strictly treated as unavailable and does NOT increase risk.",
            "methodology_disclaimer": SCORING_METHODOLOGY_DISCLAIMER,
        }

        # 5. Generate Actionable Recommendations based on findings
        recommendations = self._generate_recommendations(
            score=final_score,
            severity=severity,
            category_points=capped_category_points,
            signals=deduplicated_signals,
        )

        return RiskScoringResult(
            risk_score=final_score,
            severity=severity,
            model_version=self.rule_version,
            confidence=confidence,
            indicators=contributing_indicators,
            explanation=explanation,
            recommendations=recommendations,
        )

    def _generate_recommendations(
        self,
        score: float,
        severity: RiskSeverity,
        category_points: Dict[str, float],
        signals: List[SignalItem],
    ) -> List[Dict[str, Any]]:
        """Synthesize tailored recommendations based on detected signals."""
        recs: List[Dict[str, Any]] = []
        added_actions: Set[str] = set()

        def add_rec(key: str) -> None:
            if key in STANDARD_RECOMMENDATIONS and key not in added_actions:
                recs.append(STANDARD_RECOMMENDATIONS[key])
                added_actions.add(key)

        # High or critical severity actions
        if severity == RiskSeverity.CRITICAL or score >= 80.0:
            add_rec("REQUEST_TAKEDOWN_REVIEW")
            add_rec("ESCALATE_MANUAL_REVIEW")
        elif severity == RiskSeverity.HIGH or score >= 60.0:
            add_rec("ESCALATE_MANUAL_REVIEW")
            add_rec("COLLECT_ADDITIONAL_EVIDENCE")

        # Category specific recommendations
        if category_points.get("DOMAIN_SIMILARITY", 0.0) > 0.0:
            add_rec("VERIFY_DOMAIN_OWNERSHIP")

        if (
            category_points.get("SCAM_AND_CREDENTIAL_HARVESTING", 0.0) > 0.0
            or category_points.get("VISUAL_SIMILARITY", 0.0) > 0.0
        ):
            add_rec("MONITOR_REPEATED_IMPERSONATION")
            add_rec("COLLECT_ADDITIONAL_EVIDENCE")

        if category_points.get("THREAT_INTELLIGENCE", 0.0) > 0.0:
            add_rec("REQUEST_TAKEDOWN_REVIEW")

        # Low risk default
        if not recs or severity == RiskSeverity.LOW:
            add_rec("ROUTINE_MONITORING")

        return recs
