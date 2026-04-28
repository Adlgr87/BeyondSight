"""
BeyondSight — PVU Metrics
=========================
Computes core performance metrics used in the PVU validation protocol:
  - MAE, RMSE, MAPE
  - Directional Accuracy
  - Turning-Point F1 / Timing Error (Tipping Forecast Skill)

All functions accept plain Python lists or numpy arrays.
"""
from __future__ import annotations

import math
from typing import Sequence


def _arr(x: Sequence[float]) -> list[float]:
    return [float(v) for v in x]


# ---------------------------------------------------------------------------
# Point-forecast metrics
# ---------------------------------------------------------------------------

def mae(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
    """Mean Absolute Error."""
    t, p = _arr(y_true), _arr(y_pred)
    return sum(abs(a - b) for a, b in zip(t, p)) / len(t)


def rmse(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
    """Root Mean Squared Error."""
    t, p = _arr(y_true), _arr(y_pred)
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(t, p)) / len(t))


def mape(y_true: Sequence[float], y_pred: Sequence[float], eps: float = 1e-8) -> float:
    """Mean Absolute Percentage Error (skips near-zero actuals)."""
    t, p = _arr(y_true), _arr(y_pred)
    valid = [(a, b) for a, b in zip(t, p) if abs(a) > eps]
    if not valid:
        return float("nan")
    return sum(abs(a - b) / abs(a) for a, b in valid) / len(valid)


def directional_accuracy(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
    """Fraction of steps where the predicted direction matches the actual direction."""
    t, p = _arr(y_true), _arr(y_pred)
    if len(t) < 2:
        return float("nan")
    correct = sum(
        1
        for i in range(1, len(t))
        if (t[i] - t[i - 1]) * (p[i] - p[i - 1]) >= 0
    )
    return correct / (len(t) - 1)


# ---------------------------------------------------------------------------
# Turning-point (tipping) skill
# ---------------------------------------------------------------------------

def turning_point_f1(
    true_events: Sequence[int],
    pred_events: Sequence[int],
    tolerance: int = 1,
) -> float:
    """
    F1 score for turning-point detection.

    Parameters
    ----------
    true_events : list of int
        Timestep indices where a turning-point actually occurs.
    pred_events : list of int
        Timestep indices where the model predicts a turning-point.
    tolerance : int
        A prediction is considered a hit if it falls within ±tolerance steps
        of any true event.
    """
    if not true_events and not pred_events:
        return 1.0
    if not true_events or not pred_events:
        return 0.0

    matched_true: set[int] = set()
    tp = 0
    for pred in pred_events:
        for true in true_events:
            if abs(pred - true) <= tolerance and true not in matched_true:
                tp += 1
                matched_true.add(true)
                break

    precision = tp / len(pred_events) if pred_events else 0.0
    recall = tp / len(true_events) if true_events else 0.0
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def turning_point_timing_error(
    true_events: Sequence[int],
    pred_events: Sequence[int],
) -> float:
    """
    Mean absolute timing error between matched true/predicted turning-points.
    Returns NaN when no matches exist.
    """
    if not true_events or not pred_events:
        return float("nan")

    errors: list[float] = []
    used: set[int] = set()
    for true in true_events:
        best: float | None = None
        best_pred: int | None = None
        for pred in pred_events:
            if pred not in used:
                d = abs(pred - true)
                if best is None or d < best:
                    best = float(d)
                    best_pred = pred
        if best_pred is not None:
            errors.append(best)
            used.add(best_pred)

    return sum(errors) / len(errors) if errors else float("nan")


# ---------------------------------------------------------------------------
# Summary helper
# ---------------------------------------------------------------------------

def compute_all(
    y_true: Sequence[float],
    y_pred: Sequence[float],
    true_events: Sequence[int] | None = None,
    pred_events: Sequence[int] | None = None,
    tp_tolerance: int = 1,
) -> dict:
    """Return a dict of all PVU metrics."""
    result: dict = {
        "mae": mae(y_true, y_pred),
        "rmse": rmse(y_true, y_pred),
        "mape": mape(y_true, y_pred),
        "directional_accuracy": directional_accuracy(y_true, y_pred),
    }
    te = true_events or []
    pe = pred_events or []
    result["turning_point_f1"] = turning_point_f1(te, pe, tolerance=tp_tolerance)
    result["turning_point_timing_error"] = turning_point_timing_error(te, pe)
    return result
