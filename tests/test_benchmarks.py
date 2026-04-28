"""
tests/test_benchmarks.py — Minimal tests for the PVU-BS benchmark package.

These tests validate that:
1. Sample cases can be loaded and validated by benchmarks/io.py.
2. All baselines can fit and predict without errors.
3. Metrics functions return expected types and ranges.
4. Turning-point detection returns valid results.
5. The runner produces output files from sample cases.
"""
import json
import os
import sys
import unittest

import numpy as np

# Ensure project root is in path when running directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
SAMPLE_CASES_DIR = os.path.join(REPO_ROOT, "datasets", "pvu_cases")


class TestPVUCaseLoading(unittest.TestCase):
    """Test that sample cases load correctly via benchmarks.io."""

    def test_load_all_sample_cases(self):
        from benchmarks.io import load_cases
        cases = load_cases(SAMPLE_CASES_DIR)
        self.assertGreaterEqual(len(cases), 1, "At least one sample case must load.")

    def test_case_has_required_fields(self):
        from benchmarks.io import load_cases
        cases = load_cases(SAMPLE_CASES_DIR)
        for case in cases:
            self.assertIsNotNone(case.case_id)
            self.assertIsNotNone(case.meta)
            self.assertIsNotNone(case.timeseries)
            self.assertIsNotNone(case.interventions)
            self.assertIsNotNone(case.network)

    def test_polarization_in_range(self):
        from benchmarks.io import load_cases
        cases = load_cases(SAMPLE_CASES_DIR)
        for case in cases:
            pol = np.asarray(case.timeseries["polarization"], dtype=float)
            self.assertTrue(
                np.all(pol >= 0) and np.all(pol <= 1),
                f"Case {case.case_id}: polarization out of [0,1]",
            )

    def test_meta_synthetic_flag(self):
        from benchmarks.io import load_cases
        cases = load_cases(SAMPLE_CASES_DIR)
        for case in cases:
            self.assertTrue(
                case.meta.get("is_synthetic"),
                f"Sample case {case.case_id} should have is_synthetic=True",
            )

    def test_load_single_case(self):
        from benchmarks.io import load_case
        case_dir = os.path.join(SAMPLE_CASES_DIR, "sample_case_001")
        if not os.path.isdir(case_dir):
            self.skipTest("sample_case_001 not found")
        case = load_case(case_dir)
        self.assertEqual(case.case_id, "sample_case_001")


class TestBaselines(unittest.TestCase):
    """Test that all baselines fit and produce valid predictions."""

    @classmethod
    def setUpClass(cls):
        cls.rng = np.random.default_rng(0)
        cls.y_train = cls.rng.uniform(0.2, 0.8, size=40)
        cls.n_steps = 10

    def _check_predictions(self, preds, name):
        self.assertEqual(len(preds), self.n_steps, f"{name}: wrong number of predictions")
        self.assertTrue(np.all(np.isfinite(preds)), f"{name}: predictions contain non-finite values")

    def test_naive_baseline(self):
        from benchmarks.baselines import NaiveBaseline
        bl = NaiveBaseline()
        bl.fit(self.y_train)
        preds = bl.predict(self.n_steps)
        self._check_predictions(preds, "NaiveBaseline")
        self.assertTrue(np.allclose(preds, self.y_train[-1]))

    def test_moving_average_baseline(self):
        from benchmarks.baselines import MovingAverageBaseline
        bl = MovingAverageBaseline(window=5)
        bl.fit(self.y_train)
        preds = bl.predict(self.n_steps)
        self._check_predictions(preds, "MovingAverageBaseline")

    def test_ar1_baseline(self):
        from benchmarks.baselines import AR1Baseline
        bl = AR1Baseline()
        bl.fit(self.y_train)
        preds = bl.predict(self.n_steps)
        self._check_predictions(preds, "AR1Baseline")
        # predictions should be clipped to [0, 1]
        self.assertTrue(np.all(preds >= 0) and np.all(preds <= 1))

    def test_random_regime_baseline(self):
        from benchmarks.baselines import RandomRegimeBaseline
        bl = RandomRegimeBaseline(seed=42)
        bl.fit(self.y_train)
        preds = bl.predict(self.n_steps)
        self._check_predictions(preds, "RandomRegimeBaseline")

    def test_degroot_only_baseline(self):
        from benchmarks.baselines import DeGrootOnlyBaseline
        bl = DeGrootOnlyBaseline(seed=42)
        bl.fit(self.y_train)
        preds = bl.predict(self.n_steps)
        self._check_predictions(preds, "DeGrootOnlyBaseline")

    def test_get_all_baselines(self):
        from benchmarks.baselines import get_all_baselines
        baselines = get_all_baselines(seed=0)
        self.assertEqual(len(baselines), 5)
        names = [b.name for b in baselines]
        self.assertIn("naive", names)
        self.assertIn("ar1", names)
        self.assertIn("degroot_only", names)


class TestMetrics(unittest.TestCase):
    """Test metric functions with known inputs."""

    def test_mae_perfect(self):
        from benchmarks.metrics import mae
        y = np.array([0.1, 0.5, 0.9])
        self.assertAlmostEqual(mae(y, y), 0.0)

    def test_mae_known(self):
        from benchmarks.metrics import mae
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.5, 2.5, 3.5])
        self.assertAlmostEqual(mae(y_true, y_pred), 0.5)

    def test_rmse_known(self):
        from benchmarks.metrics import rmse
        y_true = np.array([0.0, 0.0])
        y_pred = np.array([1.0, 1.0])
        self.assertAlmostEqual(rmse(y_true, y_pred), 1.0)

    def test_mape_near_zero(self):
        from benchmarks.metrics import mape
        # Small values should be skipped
        y_true = np.array([1e-9, 1.0])
        y_pred = np.array([0.0, 0.8])
        result = mape(y_true, y_pred)
        # Only second element used: |1.0 - 0.8| / 1.0 = 20%
        self.assertAlmostEqual(result, 20.0, places=5)

    def test_directional_accuracy(self):
        from benchmarks.metrics import directional_accuracy
        y_true = np.array([0.1, 0.3, 0.2, 0.5])
        y_pred = np.array([0.1, 0.4, 0.1, 0.6])
        # Deltas true: +, -, +; pred: +, -, +
        da = directional_accuracy(y_true, y_pred)
        self.assertAlmostEqual(da, 1.0)

    def test_compute_all_returns_dict(self):
        from benchmarks.metrics import compute_all
        y = np.random.default_rng(0).uniform(0.2, 0.8, 20)
        result = compute_all(y, y * 0.9)
        for key in ("mae", "rmse", "mape", "da"):
            self.assertIn(key, result)
            self.assertIsInstance(result[key], float)

    def test_holm_bonferroni(self):
        from benchmarks.metrics import holm_bonferroni
        pvals = [0.01, 0.04, 0.03]
        thresholds = holm_bonferroni(pvals, alpha=0.05)
        self.assertEqual(len(thresholds), len(pvals))
        # All thresholds should be positive
        self.assertTrue(all(t > 0 for t in thresholds))


class TestTurningPoints(unittest.TestCase):
    """Test turning-point detection and scoring."""

    def test_detect_simple_max_min(self):
        from benchmarks.turning_points import detect_turning_points
        series = np.array([0.2, 0.5, 0.8, 0.5, 0.2, 0.5, 0.8])
        tps = detect_turning_points(series, delta_min=0.1, gap_min=2)
        # Should detect the max at index 2
        self.assertIn(2, tps)

    def test_detect_empty_short_series(self):
        from benchmarks.turning_points import detect_turning_points
        tps = detect_turning_points(np.array([0.5, 0.6]), delta_min=0.05, gap_min=3)
        self.assertEqual(len(tps), 0)

    def test_score_perfect_match(self):
        from benchmarks.turning_points import score_turning_points
        y = np.array([0.2, 0.5, 0.8, 0.4, 0.1, 0.4, 0.7, 0.4, 0.2])
        result = score_turning_points(y, y, delta_min=0.1, gap_min=2, tau=2)
        self.assertGreaterEqual(result["f1"], 0.0)
        self.assertLessEqual(result["f1"], 1.0)

    def test_score_no_turning_points(self):
        from benchmarks.turning_points import score_turning_points
        y = np.linspace(0.2, 0.8, 20)  # monotone — no turning points
        result = score_turning_points(y, y, delta_min=0.05, gap_min=3, tau=2)
        self.assertEqual(result["n_true_tp"], 0)
        self.assertEqual(result["n_pred_tp"], 0)
        self.assertEqual(result["f1"], 1.0)  # both have zero TPs = perfect match


class TestRunnerEndToEnd(unittest.TestCase):
    """Integration test: runner loads cases and produces artefacts."""

    def test_runner_offline_produces_outputs(self):
        import tempfile
        from benchmarks.runner import run_benchmark

        with tempfile.TemporaryDirectory() as tmp:
            results = run_benchmark(
                cases_dir=SAMPLE_CASES_DIR,
                out_dir=tmp,
                mode="offline",
                seed=0,
                train_frac=0.6,
                val_frac=0.2,
                horizon=1,
            )
            # Check artefact files exist
            self.assertTrue(os.path.isfile(os.path.join(tmp, "metrics.json")))
            self.assertTrue(os.path.isfile(os.path.join(tmp, "report.md")))
            self.assertTrue(os.path.isfile(os.path.join(tmp, "run_meta.json")))

            # Check metrics.json is valid JSON with expected structure
            with open(os.path.join(tmp, "metrics.json"), encoding="utf-8") as f:
                metrics = json.load(f)
            self.assertIn("cases", metrics)
            self.assertGreaterEqual(len(metrics["cases"]), 1)

            # Check run_meta.json has mode
            with open(os.path.join(tmp, "run_meta.json"), encoding="utf-8") as f:
                run_meta = json.load(f)
            self.assertEqual(run_meta["mode"], "offline")

    def test_runner_returns_results_dict(self):
        import tempfile
        from benchmarks.runner import run_benchmark

        with tempfile.TemporaryDirectory() as tmp:
            results = run_benchmark(
                cases_dir=SAMPLE_CASES_DIR,
                out_dir=tmp,
                mode="offline",
                seed=42,
                train_frac=0.6,
                val_frac=0.2,
                horizon=1,
            )
        self.assertIsInstance(results, dict)
        self.assertIn("cases", results)
        self.assertIn("aggregate", results)


if __name__ == "__main__":
    unittest.main()
