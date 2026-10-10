"""Scam text classification package."""

from app.services.detection.scam_text.classifier import (
    ScamTextAnalysisResult,
    ScamTextClassifier,
)
from app.services.detection.scam_text.trainer import (
    ModelMetadata,
    train_baseline_model,
)

__all__ = [
    "ScamTextClassifier",
    "ScamTextAnalysisResult",
    "ModelMetadata",
    "train_baseline_model",
]
