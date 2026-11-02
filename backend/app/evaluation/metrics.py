"""
Evaluation Metrics Computation.
Calculates statistical regression metrics (MAE, RMSE, % improvement),
prediction interval metrics (PICP, interval width),
and anomaly detection metrics (Precision, Recall, F1, False Alert Rate, Confusion Matrix).
"""

import numpy as np
from typing import Dict, Any, List, Tuple

def compute_regression_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    baseline_mae: float = None
) -> Dict[str, float]:
    """Computes MAE, RMSE, and percentage improvement over baseline."""
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)

    errors = y_true - y_pred
    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors ** 2)))

    res = {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
    }

    if baseline_mae is not None and baseline_mae > 0:
        improvement = ((baseline_mae - mae) / baseline_mae) * 100.0
        res["improvement_pct"] = round(improvement, 2)
    else:
        res["improvement_pct"] = 0.0

    return res

def compute_interval_metrics(
    y_true: np.ndarray,
    lower_bounds: np.ndarray,
    upper_bounds: np.ndarray,
) -> Dict[str, float]:
    """Computes Prediction Interval Coverage Probability (PICP) and Mean Interval Width."""
    y_true = np.asarray(y_true, dtype=np.float64)
    lower = np.asarray(lower_bounds, dtype=np.float64)
    upper = np.asarray(upper_bounds, dtype=np.float64)

    inside = (y_true >= lower) & (y_true <= upper)
    coverage = float(np.mean(inside) * 100.0)
    avg_width = float(np.mean(upper - lower))

    return {
        "picp_coverage_pct": round(coverage, 2),
        "average_interval_width": round(avg_width, 2),
    }

def compute_anomaly_metrics(
    y_true_categories: List[str],
    y_pred_categories: List[str],
    fault_types: List[str],
) -> Dict[str, Any]:
    """
    Computes Precision, Recall, F1, False Alert Rate, Confusion Matrix,
    and per-fault recall breakdown.
    """
    categories = ["NORMAL", "GRADUAL_WEAR", "ABRUPT_ANOMALY", "INSUFFICIENT_DATA"]
    cat_to_idx = {c: i for i, c in enumerate(categories)}

    n = len(y_true_categories)
    cm = np.zeros((4, 4), dtype=int)

    for true_c, pred_c in zip(y_true_categories, y_pred_categories):
        t_idx = cat_to_idx.get(true_c, 0)
        p_idx = cat_to_idx.get(pred_c, 0)
        cm[t_idx, p_idx] += 1

    # Binary alert metrics: NORMAL (negative) vs ANY_ALERT (positive)
    is_true_alert = np.array([c != "NORMAL" for c in y_true_categories])
    is_pred_alert = np.array([c != "NORMAL" for c in y_pred_categories])

    tp = int(np.sum(is_true_alert & is_pred_alert))
    fp = int(np.sum((~is_true_alert) & is_pred_alert))
    fn = int(np.sum(is_true_alert & (~is_pred_alert)))
    tn = int(np.sum((~is_true_alert) & (~is_pred_alert)))

    precision = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    false_alert_rate = (fp / (fp + tn) * 100.0) if (fp + tn) > 0 else 0.0

    # Per-fault recall breakdown
    unique_faults = sorted(list(set(fault_types)))
    fault_breakdown = {}
    for f in unique_faults:
        f_indices = [i for i, ft in enumerate(fault_types) if ft == f]
        if not f_indices:
            continue
        f_true_alerts = is_true_alert[f_indices]
        f_pred_alerts = is_pred_alert[f_indices]
        if np.sum(f_true_alerts) > 0:
            rec = np.sum(f_true_alerts & f_pred_alerts) / np.sum(f_true_alerts)
            fault_breakdown[f] = round(float(rec * 100.0), 1)
        else:
            # For 'none' fault, calculate specificity/normal accuracy
            normal_correct = np.sum((~f_true_alerts) & (~f_pred_alerts)) / len(f_indices)
            fault_breakdown[f] = round(float(normal_correct * 100.0), 1)

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "false_alert_rate_pct": round(false_alert_rate, 2),
        "total_evaluated_instances": n,
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "per_fault_detection_pct": fault_breakdown,
        "confusion_matrix": {
            "categories": categories,
            "matrix": cm.tolist(),
        }
    }
