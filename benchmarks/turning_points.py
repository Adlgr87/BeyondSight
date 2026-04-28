"""
benchmarks/turning_points.py — Turning-point detection and scoring for PVU-BS.

A *turning point* is a local maximum or minimum in a time series P(t) with
amplitude >= delta_min and temporal separation >= gap_min steps.
"""
from __future__ import annotations

import numpy as np


def detect_turning_points(
    series: np.ndarray,
    delta_min: float = 0.05,
    gap_min: int = 3,
) -> np.ndarray:
    """Detect turning points in *series*.

    A point t is a turning point if:
    - It is a local max or min relative to its neighbours, AND
    - Its amplitude relative to the preceding turning point >= delta_min, AND
    - It is at least gap_min steps away from the previous turning point.

    Parameters
    ----------
    series:     1-D array of values (e.g. P(t)).
    delta_min:  Minimum amplitude (absolute difference from last turning point).
    gap_min:    Minimum number of steps between consecutive turning points.

    Returns
    -------
    np.ndarray
        Integer indices of detected turning points.
    """
    series = np.asarray(series, dtype=float)
    n = len(series)
    if n < 3:
        return np.array([], dtype=int)

    candidates: list[int] = []
    last_tp_idx = -gap_min  # ensure first candidate can be detected
    last_tp_val = series[0]

    for t in range(1, n - 1):
        is_max = series[t] > series[t - 1] and series[t] > series[t + 1]
        is_min = series[t] < series[t - 1] and series[t] < series[t + 1]
        if not (is_max or is_min):
            continue
        if (t - last_tp_idx) < gap_min:
            continue
        if abs(series[t] - last_tp_val) < delta_min:
            continue
        candidates.append(t)
        last_tp_idx = t
        last_tp_val = series[t]

    return np.array(candidates, dtype=int)


def score_turning_points(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    delta_min: float = 0.05,
    gap_min: int = 3,
    tau: int = 2,
) -> dict[str, float]:
    """Score turning-point predictions against ground truth.

    Parameters
    ----------
    y_true:     Ground-truth series.
    y_pred:     Predicted series.
    delta_min:  Amplitude threshold for both detection calls.
    gap_min:    Minimum gap between turning points.
    tau:        Tolerance window in steps (a match is declared if |t_pred - t_true| <= tau).

    Returns
    -------
    dict with keys:
        precision, recall, f1, mean_temporal_error,
        n_true_tp, n_pred_tp, n_matched
    """
    true_tps = detect_turning_points(y_true, delta_min=delta_min, gap_min=gap_min)
    pred_tps = detect_turning_points(y_pred, delta_min=delta_min, gap_min=gap_min)

    if len(true_tps) == 0 and len(pred_tps) == 0:
        return {
            "precision": 1.0,
            "recall": 1.0,
            "f1": 1.0,
            "mean_temporal_error": 0.0,
            "n_true_tp": 0,
            "n_pred_tp": 0,
            "n_matched": 0,
        }

    # Greedy matching: each true TP can be matched to at most one pred TP within tau
    matched_true: set[int] = set()
    matched_pred: set[int] = set()
    temporal_errors: list[float] = []

    for p_idx in pred_tps:
        best_dist = tau + 1
        best_t = -1
        for t_idx in true_tps:
            if t_idx in matched_true:
                continue
            dist = abs(int(p_idx) - int(t_idx))
            if dist <= tau and dist < best_dist:
                best_dist = dist
                best_t = t_idx
        if best_t >= 0:
            matched_true.add(best_t)
            matched_pred.add(p_idx)
            temporal_errors.append(float(best_dist))

    n_matched = len(matched_pred)
    precision = n_matched / len(pred_tps) if len(pred_tps) > 0 else 0.0
    recall = n_matched / len(true_tps) if len(true_tps) > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    mte = float(np.mean(temporal_errors)) if temporal_errors else float("nan")

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "mean_temporal_error": mte,
        "n_true_tp": int(len(true_tps)),
        "n_pred_tp": int(len(pred_tps)),
        "n_matched": n_matched,
    }
