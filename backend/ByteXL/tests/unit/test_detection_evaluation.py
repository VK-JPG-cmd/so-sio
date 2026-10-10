"""
Unit tests executing the detection pipeline evaluation benchmark.
Verifies Precision, Recall, F1 Score, and Confusion Matrix boundaries.
"""

from app.evaluation.evaluator import DetectionEvaluator


def test_detection_evaluation_benchmark_domains() -> None:
    """Verify domain threat evaluation runs deterministically with 0 false positives."""
    evaluator = DetectionEvaluator()
    summary = evaluator.evaluate_domains()

    assert summary.sample_count == 12
    assert summary.matrix.fp == 0
    assert summary.matrix.fn == 0
    assert summary.matrix.tp == 7
    assert summary.matrix.tn == 5
    assert summary.matrix.precision == 1.0
    assert summary.matrix.recall == 1.0
    assert summary.matrix.f1_score == 1.0
    assert summary.matrix.false_positive_rate == 0.0


def test_detection_evaluation_benchmark_social_profiles() -> None:
    """Verify social profile evaluation runs deterministically with 0 false positives."""
    evaluator = DetectionEvaluator()
    summary = evaluator.evaluate_social_profiles()

    assert summary.sample_count == 12
    assert summary.matrix.fp == 0
    assert summary.matrix.fn == 0
    assert summary.matrix.tp == 7
    assert summary.matrix.tn == 5
    assert summary.matrix.precision == 1.0
    assert summary.matrix.recall == 1.0
    assert summary.matrix.f1_score == 1.0
    assert summary.matrix.false_positive_rate == 0.0


def test_detection_evaluation_benchmark_app_metadata() -> None:
    """Verify app metadata evaluation runs deterministically with 0 false positives."""
    evaluator = DetectionEvaluator()
    summary = evaluator.evaluate_app_metadata()

    assert summary.sample_count == 11
    assert summary.matrix.fp == 0
    assert summary.matrix.fn == 0
    assert summary.matrix.tp == 7
    assert summary.matrix.tn == 4
    assert summary.matrix.precision == 1.0
    assert summary.matrix.recall == 1.0
    assert summary.matrix.f1_score == 1.0
    assert summary.matrix.false_positive_rate == 0.0
