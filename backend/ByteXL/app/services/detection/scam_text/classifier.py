"""
Scam text inference engine.
Combines machine learning classification with transparent rule-based risk indicators.
Separated strictly from model training.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.services.detection.scam_text.trainer import (
    ModelMetadata,
    preprocess_text,
    train_baseline_model,
)

# Transparent rule-based scam indicators
URGENCY_KEYWORDS = [
    "urgent", "immediately", "immediate action", "account locked",
    "account suspended", "act now", "final notice", "terminated",
    "within 24 hours", "unusual activity", "limited time",
]

FINANCIAL_SCAM_KEYWORDS = [
    "bitcoin", "crypto", "ethereum", "gift card", "wire transfer",
    "refund", "lottery", "unclaimed prize", "customs fee", "smart contract",
]

CREDENTIAL_THEFT_KEYWORDS = [
    "verify your identity", "social security number", "confirm your password",
    "verification code", "one-time code", "send otp", "enter your pin",
]


class ScamTextAnalysisResult(BaseModel):
    """Evaluation result for scam/phishing message classification."""

    model_config = ConfigDict(protected_namespaces=())

    raw_text: str
    preprocessed_text: str
    is_scam: bool
    scam_probability: float = Field(..., ge=0.0, le=1.0)
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL

    # Transparent rule-based indicators
    urgency_indicators: List[str] = Field(default_factory=list)
    financial_indicators: List[str] = Field(default_factory=list)
    credential_indicators: List[str] = Field(default_factory=list)
    contains_links: bool = False

    # Model metadata and limitations
    model_metadata: ModelMetadata


class ScamTextClassifier:
    """Inference service for scam and fraudulent text detection."""

    def __init__(self) -> None:
        # Load and train development baseline in-memory
        self.model, self.metadata = train_baseline_model()

    def classify_text(self, text: str) -> ScamTextAnalysisResult:
        """Execute text classification and extract transparent heuristic indicators."""
        clean = preprocess_text(text)
        lower_raw = text.lower()

        # 1. Machine Learning Inference
        probabilities = self.model.predict_proba([clean])[0]
        # Class 1 is scam
        scam_prob = float(probabilities[1])

        # 2. Extract Transparent Rule-Based Indicators
        found_urgency = [w for w in URGENCY_KEYWORDS if w in lower_raw]
        found_financial = [w for w in FINANCIAL_SCAM_KEYWORDS if w in lower_raw]
        found_credentials = [w for w in CREDENTIAL_THEFT_KEYWORDS if w in lower_raw]
        has_links = "<url>" in clean or "http" in lower_raw or "www." in lower_raw

        # 3. Composite score combining ML probability and rule-based heuristics
        rule_boost = 0.0
        if found_urgency:
            rule_boost += 0.15
        if found_financial:
            rule_boost += 0.20
        if found_credentials:
            rule_boost += 0.25
        if has_links and (found_urgency or found_credentials):
            rule_boost += 0.20

        composite_prob = min(max(scam_prob + rule_boost, 0.0), 1.0)
        is_scam = composite_prob >= 0.50

        if composite_prob >= 0.75:
            risk_level = "CRITICAL"
        elif composite_prob >= 0.55:
            risk_level = "HIGH"
        elif composite_prob >= 0.50:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return ScamTextAnalysisResult(
            raw_text=text,
            preprocessed_text=clean,
            is_scam=is_scam,
            scam_probability=round(composite_prob, 4),
            risk_level=risk_level,
            urgency_indicators=found_urgency,
            financial_indicators=found_financial,
            credential_indicators=found_credentials,
            contains_links=has_links,
            model_metadata=self.metadata,
        )
