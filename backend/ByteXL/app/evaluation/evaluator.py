"""
Detection Quality Evaluation Engine for BrandShield AI.
Calculates Precision, Recall, F1 Score, False-Positive Rate,
and Confusion Matrices across Domain, Social Profile, and App Metadata detectors.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from app.evaluation.dataset import (
    EVAL_BRAND,
    SYNTHETIC_APP_METADATA,
    SYNTHETIC_DOMAINS,
    SYNTHETIC_SOCIAL_PROFILES,
)
from app.models.enums import RiskSeverity
from app.schemas.app_metadata import AppMetadataAnalysisRequest
from app.services.detection.app_metadata_analysis import AppMetadataAnalysisService
from app.services.detection.domain_analysis import DomainAnalysisService
from app.services.detection.profile_analysis import ProfileAnalysisService, SocialProfileInput


@dataclass
class ConfusionMatrix:
    """Confusion matrix counts."""
    tp: int = 0
    fp: int = 0
    tn: int = 0
    fn: int = 0

    @property
    def total(self) -> int:
        return self.tp + self.fp + self.tn + self.fn

    @property
    def precision(self) -> float:
        denom = self.tp + self.fp
        return round(self.tp / denom, 4) if denom > 0 else 1.0

    @property
    def recall(self) -> float:
        denom = self.tp + self.fn
        return round(self.tp / denom, 4) if denom > 0 else 1.0

    @property
    def f1_score(self) -> float:
        p = self.precision
        r = self.recall
        denom = p + r
        return round((2 * p * r) / denom, 4) if denom > 0 else 0.0

    @property
    def false_positive_rate(self) -> float:
        denom = self.fp + self.tn
        return round(self.fp / denom, 4) if denom > 0 else 0.0

    @property
    def accuracy(self) -> float:
        denom = self.total
        return round((self.tp + self.tn) / denom, 4) if denom > 0 else 0.0


@dataclass
class EvaluationSummary:
    """Evaluation summary results for a detection module."""
    module_name: str
    sample_count: int
    matrix: ConfusionMatrix
    detailed_results: List[Dict[str, Any]]


class DetectionEvaluator:
    """Orchestrates deterministic detection quality benchmarking."""

    def __init__(self) -> None:
        self.domain_service = DomainAnalysisService()
        self.profile_service = ProfileAnalysisService()
        self.app_service = AppMetadataAnalysisService()

    def evaluate_domains(self) -> EvaluationSummary:
        """Run evaluation on synthetic domains dataset."""
        matrix = ConfusionMatrix()
        details: List[Dict[str, Any]] = []

        for item in SYNTHETIC_DOMAINS:
            res = self.domain_service.analyze_domain(item["domain"], [EVAL_BRAND])
            # Malicious if score >= 25.0 (MEDIUM+) or if flagged with high-confidence indicators
            pred_malicious = res.risk_score >= 25.0 and not (res.is_official_domain and res.risk_score == 0.0)
            actual_malicious = item["is_malicious"]

            if actual_malicious and pred_malicious:
                matrix.tp += 1
                outcome = "TP"
            elif not actual_malicious and pred_malicious:
                matrix.fp += 1
                outcome = "FP"
            elif not actual_malicious and not pred_malicious:
                matrix.tn += 1
                outcome = "TN"
            else:
                matrix.fn += 1
                outcome = "FN"

            details.append({
                "id": item["id"],
                "target": item["domain"],
                "category": item["category"],
                "actual": actual_malicious,
                "predicted": pred_malicious,
                "risk_score": res.risk_score,
                "risk_level": res.risk_level,
                "outcome": outcome,
            })

        return EvaluationSummary(
            module_name="Domain Threat Detection",
            sample_count=len(SYNTHETIC_DOMAINS),
            matrix=matrix,
            detailed_results=details,
        )

    def evaluate_social_profiles(self) -> EvaluationSummary:
        """Run evaluation on synthetic social profiles dataset."""
        matrix = ConfusionMatrix()
        details: List[Dict[str, Any]] = []

        for item in SYNTHETIC_SOCIAL_PROFILES:
            inp = SocialProfileInput(
                platform=item["platform"],
                username=item["username"],
                display_name=item["display_name"],
                bio=item.get("bio"),
                external_links=item.get("external_links", []),
                avatar_hash=item.get("avatar_hash"),
            )
            res = self.profile_service.analyze_profile(inp, [EVAL_BRAND])
            pred_malicious = res.risk_score >= 25.0 and not (res.is_official_account and res.risk_score == 0.0)
            actual_malicious = item["is_malicious"]

            if actual_malicious and pred_malicious:
                matrix.tp += 1
                outcome = "TP"
            elif not actual_malicious and pred_malicious:
                matrix.fp += 1
                outcome = "FP"
            elif not actual_malicious and not pred_malicious:
                matrix.tn += 1
                outcome = "TN"
            else:
                matrix.fn += 1
                outcome = "FN"

            details.append({
                "id": item["id"],
                "target": item["username"],
                "category": item["category"],
                "actual": actual_malicious,
                "predicted": pred_malicious,
                "risk_score": res.risk_score,
                "risk_level": res.risk_level,
                "outcome": outcome,
            })

        return EvaluationSummary(
            module_name="Social Profile Impersonation Detection",
            sample_count=len(SYNTHETIC_SOCIAL_PROFILES),
            matrix=matrix,
            detailed_results=details,
        )

    def evaluate_app_metadata(self) -> EvaluationSummary:
        """Run evaluation on synthetic mobile app metadata dataset."""
        matrix = ConfusionMatrix()
        details: List[Dict[str, Any]] = []

        for item in SYNTHETIC_APP_METADATA:
            req = AppMetadataAnalysisRequest(
                brand_id=EVAL_BRAND.brand_id,
                app_name=item["app_name"],
                platform=item["platform"],
                app_identifier=item["app_identifier"],
                publisher_name=item.get("publisher_name"),
                description=item.get("description"),
                store_url=item.get("store_url"),
                logo_hash=item.get("logo_hash"),
            )
            res = self.app_service.analyze_metadata(req, EVAL_BRAND)
            pred_malicious = res.risk_score >= 25.0 and not (res.is_official_match and res.risk_score == 0.0)
            actual_malicious = item["is_malicious"]

            if actual_malicious and pred_malicious:
                matrix.tp += 1
                outcome = "TP"
            elif not actual_malicious and pred_malicious:
                matrix.fp += 1
                outcome = "FP"
            elif not actual_malicious and not pred_malicious:
                matrix.tn += 1
                outcome = "TN"
            else:
                matrix.fn += 1
                outcome = "FN"

            details.append({
                "id": item["id"],
                "target": f"{item['app_name']} ({item['app_identifier']})",
                "category": item["category"],
                "actual": actual_malicious,
                "predicted": pred_malicious,
                "risk_score": res.risk_score,
                "severity": res.severity.value,
                "outcome": outcome,
            })

        return EvaluationSummary(
            module_name="App Store Listing Metadata Detection",
            sample_count=len(SYNTHETIC_APP_METADATA),
            matrix=matrix,
            detailed_results=details,
        )

    def run_all(self) -> Dict[str, EvaluationSummary]:
        """Execute full evaluation across all detection modules."""
        return {
            "domains": self.evaluate_domains(),
            "social_profiles": self.evaluate_social_profiles(),
            "app_metadata": self.evaluate_app_metadata(),
        }
