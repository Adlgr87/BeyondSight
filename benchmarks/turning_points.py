"""
BeyondSight — PVU Turning-Point Detection
==========================================
Detects turning-points (tipping events / phase transitions) in a time series
and computes the Tipping Forecast Skill metrics used in PVU validation.

A turning-point at timestep t is defined as a local extremum where the series
changes direction with a magnitude exceeding `threshold` × series std-dev.
"""
from __future__ import annotations

import statistics
from typing import Sequence


def detect_turning_points(
    series: Sequence[float],
    threshold: float = 0.5,
    min_gap: int = 2,
) -> list[int]:
    """
    Detect turning-point indices in a time series.

    Parameters
    ----------
    series : sequence of float
        The polarization (or target) time-series.
    threshold : float
        A local extremum must exceed `threshold` × std_dev of first-differences
        to be counted as a turning-point.
    min_gap : int
        Minimum number of steps between successive turning-points.

    Returns
    -------
    list of int
        Indices (0-based) of detected turning-points.
    """
    s = [float(v) for v in series]
    n = len(s)
    if n < 3:
        return []

    diffs = [s[i + 1] - s[i] for i in range(n - 1)]
    if len(diffs) < 2:
        return []

    try:
        std_diff = statistics.stdev(diffs)
    except statistics.StatisticsError:
        std_diff = 0.0

    cutoff = threshold * std_diff if std_diff > 0 else 0.0

    events: list[int] = []
    last_event = -min_gap - 1

    for i in range(1, n - 1):
        delta_before = s[i] - s[i - 1]
        delta_after = s[i + 1] - s[i]
        # Direction change
        is_peak = delta_before > 0 and delta_after < 0
        is_trough = delta_before < 0 and delta_after > 0
        if (is_peak or is_trough) and abs(delta_before) >= cutoff:
            if i - last_event >= min_gap:
                events.append(i)
                last_event = i

    return events


def score_turning_points(
    true_series: Sequence[float],
    pred_series: Sequence[float],
    threshold: float = 0.5,
    min_gap: int = 2,
    tolerance: int = 1,
) -> dict:
    """
    Detect turning-points in both series and compute Tipping Forecast Skill.

    Returns
    -------
    dict with keys: true_events, pred_events, f1, timing_error
    """
    from benchmarks.metrics import turning_point_f1, turning_point_timing_error

    true_events = detect_turning_points(true_series, threshold=threshold, min_gap=min_gap)
    pred_events = detect_turning_points(pred_series, threshold=threshold, min_gap=min_gap)
    f1 = turning_point_f1(true_events, pred_events, tolerance=tolerance)
    timing_err = turning_point_timing_error(true_events, pred_events)

    return {
        "true_events": true_events,
        "pred_events": pred_events,
        "f1": f1,
        "timing_error": timing_err,
    }
