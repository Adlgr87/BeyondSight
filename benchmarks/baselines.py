"""
BeyondSight — PVU Baselines
============================
Reference forecasters used in PVU validation:

  naive          — y_hat(t) = y(t-1)  (random-walk / no-change)
  moving_average — y_hat(t) = mean(y[t-window:t])
  ar1            — AR(1): OLS fit on training data, applied to test
  random_regime  — samples uniformly from the training distribution
  degroot        — mean-field DeGroot (constant convergence to mean)

All predictors expose a fit(train) / predict(n_steps, last_y) interface.
"""
from __future__ import annotations

import random
import statistics
from typing import Sequence


class NaiveBaseline:
    """Persists the last observed value."""

    name = "naive"

    def fit(self, train: Sequence[float]) -> "NaiveBaseline":
        self._last = float(train[-1])
        return self

    def predict(self, n_steps: int, last_y: float | None = None) -> list[float]:
        start = last_y if last_y is not None else self._last
        return [start] * n_steps


class MovingAverageBaseline:
    """Predicts the rolling mean of the last `window` observations."""

    name = "moving_average"

    def __init__(self, window: int = 5) -> None:
        self.window = window
        self._history: list[float] = []

    def fit(self, train: Sequence[float]) -> "MovingAverageBaseline":
        self._history = list(train)
        return self

    def predict(self, n_steps: int, last_y: float | None = None) -> list[float]:
        history = list(self._history)
        if last_y is not None:
            history.append(last_y)
        preds: list[float] = []
        for _ in range(n_steps):
            window_vals = history[-self.window :]
            p = statistics.mean(window_vals)
            preds.append(p)
            history.append(p)
        return preds


class AR1Baseline:
    """AR(1) model fitted via OLS on the training series."""

    name = "ar1"

    def __init__(self) -> None:
        self._alpha = 0.0
        self._beta = 1.0

    def fit(self, train: Sequence[float]) -> "AR1Baseline":
        t = [float(v) for v in train]
        if len(t) < 2:
            self._alpha, self._beta = 0.0, 1.0
            return self
        x = t[:-1]
        y = t[1:]
        n = len(x)
        xbar, ybar = sum(x) / n, sum(y) / n
        ss_xx = sum((xi - xbar) ** 2 for xi in x)
        ss_xy = sum((xi - xbar) * (yi - ybar) for xi, yi in zip(x, y))
        if ss_xx == 0:
            self._alpha, self._beta = ybar, 0.0
        else:
            self._beta = ss_xy / ss_xx
            self._alpha = ybar - self._beta * xbar
        self._last = t[-1]
        return self

    def predict(self, n_steps: int, last_y: float | None = None) -> list[float]:
        current = last_y if last_y is not None else self._last
        preds: list[float] = []
        for _ in range(n_steps):
            current = self._alpha + self._beta * current
            preds.append(current)
        return preds


class RandomRegimeBaseline:
    """Samples uniformly from the empirical training distribution."""

    name = "random_regime"

    def __init__(self, seed: int = 42) -> None:
        self._rng = random.Random(seed)
        self._pool: list[float] = []

    def fit(self, train: Sequence[float]) -> "RandomRegimeBaseline":
        self._pool = [float(v) for v in train]
        return self

    def predict(self, n_steps: int, last_y: float | None = None) -> list[float]:
        return [self._rng.choice(self._pool) for _ in range(n_steps)]


class DeGrootBaseline:
    """
    Mean-field DeGroot: opinions converge monotonically toward the group mean.
    This is the 'pure averaging' model without BeyondSight's regime detection.
    """

    name = "degroot"

    def __init__(self, alpha: float = 0.1) -> None:
        self.alpha = alpha  # convergence speed per step
        self._mean = 0.0

    def fit(self, train: Sequence[float]) -> "DeGrootBaseline":
        t = [float(v) for v in train]
        self._mean = sum(t) / len(t)
        self._last = t[-1]
        return self

    def predict(self, n_steps: int, last_y: float | None = None) -> list[float]:
        current = last_y if last_y is not None else self._last
        preds: list[float] = []
        for _ in range(n_steps):
            current = current + self.alpha * (self._mean - current)
            preds.append(current)
        return preds


# Convenience registry
ALL_BASELINES: dict[str, type] = {
    "naive": NaiveBaseline,
    "moving_average": MovingAverageBaseline,
    "ar1": AR1Baseline,
    "random_regime": RandomRegimeBaseline,
    "degroot": DeGrootBaseline,
}
