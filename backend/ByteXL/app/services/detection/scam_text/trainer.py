"""
Scam text classifier training module.
Trains a scikit-learn TF-IDF + LogisticRegression pipeline on development data.
Evaluates model performance and exports standardized model metadata.
"""

from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Tuple
from pydantic import BaseModel, ConfigDict, Field
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.pipeline import Pipeline
from app.core.logging import get_logger
from app.services.detection.scam_text.dataset import DEVELOPMENT_SCAM_DATASET

logger = get_logger("app.services.detection.scam_text.trainer")


class ModelMetadata(BaseModel):
    """Provenance and evaluation record for the text classifier."""

    model_config = ConfigDict(protected_namespaces=())

    model_version: str = "0.1.0-baseline-dev"
    trained_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    input_preprocessing: str = (
        "Lowercase conversion, URL/link tokenization to <URL>, phone normalization "
        "to <PHONE>, currency normalization to <CURRENCY>, and non-alphanumeric stripping."
    )
    training_data_source: str = (
        "BrandShield AI curated development benchmark dataset (synthetic and "
        "representative real-world scam / legitimate message pairs)."
    )
    sample_count: int
    evaluation_metrics: Dict[str, float]
    known_limitations: str = (
        "Known limitations include: "
        "1. Trained on a small developmental benchmark dataset; not intended for production "
        "zero-day scam detection without active human moderation. "
        "2. Highly sensitive to novel vocabulary and multilingual adversarial evasion. "
        "3. Complemented by rule-based indicator checks for high-urgency keywords."
    )


def preprocess_text(text: str) -> str:
    """Preprocess text by lowercasing and abstracting links and numbers into standard tokens."""
    if not text:
        return ""
    t = text.lower()
    # Normalize URLs
    t = re.sub(r"https?://\S+|www\.\S+", "<url>", t)
    # Normalize phone numbers
    t = re.sub(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "<phone>", t)
    # Normalize dollar and crypto currency amounts
    t = re.sub(r"[\$€£]\d+(?:,\d{3})*(?:\.\d+)?", "<currency>", t)
    # Strip excessive punctuation
    t = re.sub(r"[^\w\s<>]", " ", t)
    # Collapse whitespace
    t = re.sub(r"\s+", " ", t).strip()
    return t


def train_baseline_model() -> Tuple[Pipeline, ModelMetadata]:
    """
    Train a baseline TF-IDF + LogisticRegression model on the development dataset.
    Returns the fitted pipeline and its formal evaluation metadata.
    """
    texts = [item[0] for item in DEVELOPMENT_SCAM_DATASET]
    labels = [item[1] for item in DEVELOPMENT_SCAM_DATASET]

    clean_texts = [preprocess_text(t) for t in texts]

    # Create pipeline with unigram/bigram TF-IDF and balanced Logistic Regression
    pipeline = Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=500,
                sublinear_tf=True,
            ),
        ),
        (
            "clf",
            LogisticRegression(
                C=1.0,
                max_iter=200,
                class_weight="balanced",
                random_state=42,
            ),
        ),
    ])

    pipeline.fit(clean_texts, labels)

    # In-sample evaluation metrics for the development baseline
    preds = pipeline.predict(clean_texts)
    acc = float(accuracy_score(labels, preds))
    prec = float(precision_score(labels, preds, zero_division=0))
    rec = float(recall_score(labels, preds, zero_division=0))
    f1 = float(f1_score(labels, preds, zero_division=0))

    metrics = {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
    }

    metadata = ModelMetadata(
        sample_count=len(texts),
        evaluation_metrics=metrics,
    )

    logger.info(
        f"Trained scam classifier {metadata.model_version}: "
        f"Acc={acc:.2f}, F1={f1:.2f} on {len(texts)} samples."
    )

    return pipeline, metadata
