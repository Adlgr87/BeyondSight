"""
benchmarks/metrics.py — Forecast accuracy metrics for PVU-BS.

All functions accept plain numpy arrays and are dependency-free beyond numpy.
"""
from __future__ import annotations

import numpy as np


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean Absolute Error."""
    y_true, y_pred = np.asarray(y_true, dtype=float), np.asarray(y_pred, dtype=float)
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Root Mean Squared Error."""
    y_true, y_pred = np.asarray(y_true, dtype=float), np.asarray(y_pred, dtype=float)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mape(y_true: np.ndarray, y_pred: np.ndarray, eps: float = 1e-6) -> float:
    """Mean Absolute Percentage Error, robust to near-zero denominators.

    Steps where |y_true| < eps are excluded from the mean.
    Returns np.nan if no valid steps remain.
    """
    y_true, y_pred = np.asarray(y_true, dtype=float), np.asarray(y_pred, dtype=float)
    mask = np.abs(y_true) >= eps
    if not mask.any():
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def directional_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Fraction of steps where the predicted direction of change matches the true direction.

    Computes sign(Δy_true) == sign(Δy_pred) for each consecutive pair.
    Returns np.nan if there is only one observation.
    """
    y_true, y_pred = np.asarray(y_true, dtype=float), np.asarray(y_pred, dtype=float)
    if len(y_true) < 2:
        return float("nan")
    d_true = np.sign(np.diff(y_true))
    d_pred = np.sign(np.diff(y_pred))
    return float(np.mean(d_true == d_pred))


def interval_coverage(
    y_true: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
) -> float:
    """Empirical coverage of a prediction interval.

    Parameters
    ----------
    y_true:  Observed values.
    lower:   Lower bound of prediction interval.
    upper:   Upper bound of prediction interval.

    Returns
    -------
    float
        Fraction of observations inside [lower, upper].
    """
    y_true = np.asarray(y_true, dtype=float)
    lower = np.asarray(lower, dtype=float)
    upper = np.asarray(upper, dtype=float)
    return float(np.mean((y_true >= lower) & (y_true <= upper)))


def compute_all(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    lower: np.ndarray | None = None,
    upper: np.ndarray | None = None,
) -> dict[str, float]:
    """Compute the full metric suite for a forecast.

    Parameters
    ----------
    y_true:  Ground-truth values.
    y_pred:  Predicted values.
    lower:   Optional lower bound for interval coverage.
    upper:   Optional upper bound for interval coverage.

    Returns
    -------
    dict
        Keys: ``mae``, ``rmse``, ``mape``, ``da``, and optionally ``ic``.
    """
    result: dict[str, float] = {
        "mae": mae(y_true, y_pred),
        "rmse": rmse(y_true, y_pred),
        "mape": mape(y_true, y_pred),
        "da": directional_accuracy(y_true, y_pred),
    }
    if lower is not None and upper is not None:
        result["ic"] = interval_coverage(y_true, lower, upper)
    return result


# ---------------------------------------------------------------------------
# Diebold–Mariano test (simplified, no external deps)
# ---------------------------------------------------------------------------

def diebold_mariano(
    y_true: np.ndarray,
    y_pred_a: np.ndarray,
    y_pred_b: np.ndarray,
    h: int = 1,
) -> tuple[float, float]:
    """One-sided Diebold–Mariano test: H₀: MSE(A) == MSE(B), H₁: MSE(A) < MSE(B).

    Parameters
    ----------
    y_true:    Observed values.
    y_pred_a:  Predictions from model A (candidate — should be *better*).
    y_pred_b:  Predictions from model B (baseline).
    h:         Forecast horizon (used for HAC variance; default 1).

    Returns
    -------
    (dm_stat, p_value)
        ``dm_stat`` > 0 means A has lower squared error than B.
        ``p_value`` is one-sided (lower tail).
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred_a = np.asarray(y_pred_a, dtype=float)
    y_pred_b = np.asarray(y_pred_b, dtype=float)

    e_a = y_true - y_pred_a
    e_b = y_true - y_pred_b
    d = e_b ** 2 - e_a ** 2  # positive when A is better

    n = len(d)
    d_bar = np.mean(d)

    # HAC variance (Newey-West with h-1 lags)
    gamma0 = np.var(d, ddof=1)
    hac_var = gamma0
    for lag in range(1, h):
        gamma_k = np.mean((d[lag:] - d_bar) * (d[:-lag] - d_bar))
        hac_var += 2 * (1 - lag / h) * gamma_k
    hac_var = max(hac_var, 1e-12)  # numerical safety

    dm_stat = d_bar / np.sqrt(hac_var / n)

    # p-value from standard normal (one-sided: H₁: A better than B)
    p_value = _normal_sf(dm_stat)
    return float(dm_stat), float(p_value)


def _normal_sf(z: float) -> float:
    """Survival function (upper tail) of standard normal via erfc."""
    import math
    return 0.5 * math.erfc(z / math.sqrt(2))


def holm_bonferroni(p_values: list[float], alpha: float = 0.05) -> list[float]:
    """Return Holm–Bonferroni adjusted p-values (as adjusted thresholds).

    Returns a list of adjusted thresholds in the same order as p_values.
    Compare p_values[i] < adjusted_thresholds[i] to decide significance.
    """
    n = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    thresholds = [0.0] * n
    for rank, (orig_idx, _) in enumerate(indexed):
        thresholds[orig_idx] = alpha / (n - rank)
    return thresholds
