"""
Reproducible Benchmark and Detection Quality Evaluation Script.
Executes evaluation on synthetic datasets and outputs:
- Confusion Matrix (TP, FP, TN, FN)
- Precision, Recall, F1 Score
- False Positive Rate (FPR)
- Per-sample evaluation breakdown
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.evaluation.evaluator import DetectionEvaluator


def main() -> int:
    evaluator = DetectionEvaluator()
    results = evaluator.run_all()

    print("=" * 80)
    print("BRANDSHIELD AI — DETECTION QUALITY BENCHMARK EVALUATION (PHASE 4)")
    print("=" * 80)
    print()

    total_tp = 0
    total_fp = 0
    total_tn = 0
    total_fn = 0

    for key, summary in results.items():
        m = summary.matrix
        total_tp += m.tp
        total_fp += m.fp
        total_tn += m.tn
        total_fn += m.fn

        print(f"MODULE: {summary.module_name}")
        print("-" * 60)
        print(f"Sample Count: {summary.sample_count}")
        print(f"Confusion Matrix: TP={m.tp}, FP={m.fp}, TN={m.tn}, FN={m.fn}")
        print(f"Precision:           {m.precision * 100:.2f}%")
        print(f"Recall:              {m.recall * 100:.2f}%")
        print(f"F1 Score:            {m.f1_score * 100:.2f}%")
        print(f"False Positive Rate: {m.false_positive_rate * 100:.2f}%")
        print(f"Accuracy:            {m.accuracy * 100:.2f}%")
        print()
        print("  Detailed Sample Breakdown:")
        for sample in summary.detailed_results:
            status_icon = "[OK]" if sample["outcome"] in ("TP", "TN") else "[FAIL]"
            target_safe = sample['target'].encode('ascii', 'backslashreplace').decode('ascii')
            print(
                f"    {status_icon} {sample['id']}: actual={sample['actual']}, "
                f"pred={sample['predicted']} ({sample['outcome']}) | "
                f"score={sample['risk_score']} | target={target_safe}"
            )
        print()
        print("=" * 80)
        print()

    # Overall Metrics
    tot_samples = total_tp + total_fp + total_tn + total_fn
    overall_prec = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 1.0
    overall_rec = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 1.0
    overall_f1 = (2 * overall_prec * overall_rec) / (overall_prec + overall_rec) if (overall_prec + overall_rec) > 0 else 0.0
    overall_fpr = total_fp / (total_fp + total_tn) if (total_fp + total_tn) > 0 else 0.0
    overall_acc = (total_tp + total_tn) / tot_samples if tot_samples > 0 else 0.0

    print("OVERALL DETECTION PIPELINE PERFORMANCE:")
    print("-" * 60)
    print(f"Total Evaluated Samples: {tot_samples}")
    print(f"Total Confusion Matrix:  TP={total_tp}, FP={total_fp}, TN={total_tn}, FN={total_fn}")
    print(f"Overall Precision:       {overall_prec * 100:.2f}%")
    print(f"Overall Recall:          {overall_rec * 100:.2f}%")
    print(f"Overall F1 Score:        {overall_f1 * 100:.2f}%")
    print(f"Overall False Pos. Rate: {overall_fpr * 100:.2f}%")
    print(f"Overall Accuracy:        {overall_acc * 100:.2f}%")
    print("=" * 80)

    # Return failure exit code if false positives or false negatives exist
    if total_fp > 0 or total_fn > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
