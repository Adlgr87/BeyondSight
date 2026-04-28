"""
benchmarks/baselines.py — Deterministic baseline forecasters for PVU-BS.

All baselines implement the interface:
    fit(y_train: np.ndarray) -> None
    predict(n_steps: int) -> np.ndarray

They are seed-safe and dependency-free beyond numpy.
"""
from __future__ import annotations

import numpy as np


class NaiveBaseline:
    """Persist the last observed value (random-walk forecast)."""

    name = "naive"

    def __init__(self) -> None:
        self._last: float | None = None

    def fit(self, y_train: np.ndarray) -> "NaiveBaseline":
        y_train = np.asarray(y_train, dtype=float)
        self._last = float(y_train[-1])
        return self

    def predict(self, n_steps: int) -> np.ndarray:
        if self._last is None:
            raise RuntimeError("Call fit() before predict().")
        return np.full(n_steps, self._last)


class MovingAverageBaseline:
    """Rolling mean over the last *window* training observations."""

    name = "moving_average"

    def __init__(self, window: int = 5) -> None:
        self.window = window
        self._mean: float | None = None

    def fit(self, y_train: np.ndarray) -> "MovingAverageBaseline":
        y_train = np.asarray(y_train, dtype=float)
        w = min(self.window, len(y_train))
        self._mean = float(np.mean(y_train[-w:]))
        return self

    def predict(self, n_steps: int) -> np.ndarray:
        if self._mean is None:
            raise RuntimeError("Call fit() before predict().")
        return np.full(n_steps, self._mean)


class AR1Baseline:
    """AR(1) model fitted via Ordinary Least Squares.

    Equation: y_t = c + φ * y_{t-1} + ε_t
    Uses no external libraries — pure numpy OLS.
    """

    name = "ar1"

    def __init__(self) -> None:
        self._c: float = 0.0
        self._phi: float = 0.0
        self._last: float = 0.0

    def fit(self, y_train: np.ndarray) -> "AR1Baseline":
        y_train = np.asarray(y_train, dtype=float)
        if len(y_train) < 2:
            # Degenerate case: fall back to naive
            self._c = float(y_train[-1]) if len(y_train) else 0.0
            self._phi = 0.0
            self._last = self._c
            return self

        y = y_train[1:]
        X = np.column_stack([np.ones(len(y)), y_train[:-1]])
        # OLS: (X^T X)^{-1} X^T y
        XtX = X.T @ X
        Xty = X.T @ y
        try:
            coeffs = np.linalg.solve(XtX, Xty)
        except np.linalg.LinAlgError:
            coeffs = np.linalg.lstsq(X, y, rcond=None)[0]

        self._c = float(coeffs[0])
        self._phi = float(coeffs[1])
        self._last = float(y_train[-1])
        return self

    def predict(self, n_steps: int) -> np.ndarray:
        preds = np.empty(n_steps)
        y_prev = self._last
        for i in range(n_steps):
            y_next = self._c + self._phi * y_prev
            # Clip to valid range [0, 1] (polarization is bounded)
            y_next = float(np.clip(y_next, 0.0, 1.0))
            preds[i] = y_next
            y_prev = y_next
        return preds


class RandomRegimeBaseline:
    """Uniformly sample a regime (quantile bucket) and predict its mean P.

    Regimes are defined by terciles of the training set.
    Seed-fixed for reproducibility.
    """

    name = "random_regime"

    def __init__(self, seed: int = 42, n_regimes: int = 3) -> None:
        self._rng = np.random.default_rng(seed)
        self.n_regimes = n_regimes
        self._regime_means: np.ndarray | None = None

    def fit(self, y_train: np.ndarray) -> "RandomRegimeBaseline":
        y_train = np.asarray(y_train, dtype=float)
        quantiles = np.linspace(0, 100, self.n_regimes + 1)
        boundaries = np.percentile(y_train, quantiles)
        means = []
        for i in range(self.n_regimes):
            lo, hi = boundaries[i], boundaries[i + 1]
            mask = (y_train >= lo) & (y_train <= hi)
            means.append(float(np.mean(y_train[mask])) if mask.any() else float(np.mean(y_train)))
        self._regime_means = np.array(means)
        return self

    def predict(self, n_steps: int) -> np.ndarray:
        if self._regime_means is None:
            raise RuntimeError("Call fit() before predict().")
        chosen_regimes = self._rng.integers(0, self.n_regimes, size=n_steps)
        return self._regime_means[chosen_regimes]


class DeGrootOnlyBaseline:
    """Simplified DeGroot consensus model without LLM regime selection.

    Implements the basic linear averaging update rule:
        x_{t+1} = W * x_t
    where W is a row-stochastic influence matrix derived from a star topology
    with configurable self-weight.

    Used as a proxy for BeyondSight's offline mode without the LLM.
    """

    name = "degroot_only"

    def __init__(self, self_weight: float = 0.7, seed: int = 42) -> None:
        self.self_weight = float(np.clip(self_weight, 0.0, 1.0))
        self._seed = seed
        self._x0: float = 0.5
        self._n_agents: int = 5
        self._rng = np.random.default_rng(seed)

    def fit(self, y_train: np.ndarray) -> "DeGrootOnlyBaseline":
        y_train = np.asarray(y_train, dtype=float)
        # Initialise agent opinions around the last training mean
        self._x0 = float(y_train[-1]) if len(y_train) else 0.5
        # Estimate n_agents from series variance (proxy)
        variance = float(np.var(y_train)) if len(y_train) > 1 else 0.1
        self._n_agents = max(3, min(20, int(1.0 / (variance + 0.01))))
        return self

    def _make_W(self) -> np.ndarray:
        """Build a row-stochastic influence matrix (star topology)."""
        n = self._n_agents
        W = np.zeros((n, n))
        peer_weight = (1.0 - self.self_weight) / max(n - 1, 1)
        for i in range(n):
            W[i, i] = self.self_weight
            for j in range(n):
                if j != i:
                    W[i, j] = peer_weight
        return W

    def predict(self, n_steps: int) -> np.ndarray:
        n = self._n_agents
        W = self._make_W()
        # Initialise opinions with slight noise around x0
        rng = np.random.default_rng(self._seed)
        x = np.clip(
            self._x0 + rng.normal(0, 0.05, size=n),
            0.0, 1.0,
        )
        preds = np.empty(n_steps)
        theta = 0.6  # polarization threshold (matches PVU default)
        for t in range(n_steps):
            x = np.clip(W @ x, 0.0, 1.0)
            preds[t] = float(np.mean(np.abs(x) > theta))
        return preds


def get_all_baselines(seed: int = 42) -> list:
    """Return one instance of each baseline, all sharing the same seed."""
    return [
        NaiveBaseline(),
        MovingAverageBaseline(window=5),
        AR1Baseline(),
        RandomRegimeBaseline(seed=seed),
        DeGrootOnlyBaseline(seed=seed),
    ]
