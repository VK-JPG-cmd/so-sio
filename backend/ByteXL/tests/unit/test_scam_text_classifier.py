"""
Unit tests for scam text classification:
- scikit-learn TF-IDF + LogisticRegression baseline
- Training & evaluation metrics recording
- Input preprocessing
- Transparent rule-based indicator extraction
- Known limitations recording
"""

import pytest
from app.services.detection.scam_text.classifier import ScamTextClassifier
from app.services.detection.scam_text.trainer import preprocess_text, train_baseline_model


def test_preprocess_text_normalizes_entities() -> None:
    """Verify links, phone numbers, and currency are normalized into tokens."""
    raw = "Urgent: Send $500 to http://scam.org/pay or call 415-555-0199 now!"
    clean = preprocess_text(raw)

    assert "<url>" in clean
    assert "<currency>" in clean
    assert "<phone>" in clean
    assert "urgent" in clean


def test_model_training_and_metadata_provenance() -> None:
    """Verify model training records version, evaluation metrics, and limitations."""
    model, metadata = train_baseline_model()

    assert metadata.model_version == "0.1.0-baseline-dev"
    assert metadata.sample_count > 10
    assert "accuracy" in metadata.evaluation_metrics
    assert "f1_score" in metadata.evaluation_metrics
    assert metadata.evaluation_metrics["accuracy"] >= 0.80
    assert "limitations" in metadata.known_limitations.lower()


def test_scam_classification_detects_urgent_phishing() -> None:
    """Verify explicit scam text triggers high scam probability and urgency indicators."""
    classifier = ScamTextClassifier()
    scam_msg = (
        "URGENT: Your account has been suspended due to unauthorized access. "
        "Click http://bit.ly/restore-account immediately to verify your identity and enter your PIN."
    )

    result = classifier.classify_text(scam_msg)

    assert result.is_scam is True
    assert result.scam_probability >= 0.60
    assert len(result.urgency_indicators) > 0
    assert len(result.credential_indicators) > 0
    assert result.contains_links is True
    assert result.risk_level in ("HIGH", "CRITICAL")


def test_scam_classification_clears_benign_message() -> None:
    """Verify normal business/support communication is classified as clean/benign."""
    classifier = ScamTextClassifier()
    benign_msg = (
        "Hello Team, please find attached the meeting minutes and project notes "
        "from our sprint review this afternoon. Have a wonderful weekend."
    )

    result = classifier.classify_text(benign_msg)

    assert result.is_scam is False
    assert result.scam_probability < 0.50
    assert len(result.urgency_indicators) == 0
    assert len(result.financial_indicators) == 0
    assert result.risk_level == "LOW"
