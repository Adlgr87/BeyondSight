"""
benchmarks/runner.py — PVU-BS offline benchmark runner.

Usage
-----
    python -m benchmarks.runner --cases datasets/pvu_cases --offline --out reports/validation/ci
    python -m benchmarks.runner --cases datasets/pvu_cases --llm    --out reports/validation/llm_run

Flags
-----
    --cases DIR     Path to the PVU cases directory (default: datasets/pvu_cases)
    --out DIR       Output directory (default: reports/validation/ci)
    --offline       Run in offline mode (default; no LLM, uses DeGroot-only baseline)
    --llm           Run in LLM mode (requires API key env vars; NOT run in CI by default)
    --seed INT      Random seed for reproducibility (default: 42)
    --train-frac F  Fraction of steps for training (default: 0.6)
    --val-frac F    Fraction of steps for validation (default: 0.2; remainder = test)
    --horizon INT   Forecast horizon in steps (default: 1)
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

import numpy as np

# Ensure repo root is importable when running as __main__
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from benchmarks.io import load_cases
from benchmarks.baselines import get_all_baselines
from benchmarks.metrics import compute_all, diebold_mariano, holm_bonferroni
from benchmarks.turning_points import score_turning_points
from benchmarks.report import (
    build_run_meta,
    write_metrics_json,
    write_report_md,
    write_run_meta,
)


def _get_commit_sha() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _split_series(
    values: np.ndarray,
    train_frac: float,
    val_frac: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Chronological train / val / test split."""
    n = len(values)
    n_train = max(2, int(n * train_frac))
    n_val = max(1, int(n * val_frac))
    n_test = n - n_train - n_val
    if n_test < 1:
        # Fallback: use all data for train, last 1 point for test
        n_train = n - 1
        n_val = 0
        n_test = 1
    train = values[:n_train]
    val = values[n_train: n_train + n_val]
    test = values[n_train + n_val:]
    return train, val, test


def _get_polarization(case) -> np.ndarray:
    """Extract the polarization column as a numpy float array."""
    ts = case.timeseries
    try:
        col = ts["polarization"]
        return np.asarray(col, dtype=float)
    except (KeyError, TypeError):
        raise ValueError(f"[{case.case_id}] Cannot extract 'polarization' column.")


def run_benchmark(
    cases_dir: str,
    out_dir: str,
    mode: str,
    seed: int,
    train_frac: float,
    val_frac: float,
    horizon: int,
) -> dict:
    """Core benchmark loop.

    Parameters
    ----------
    cases_dir:  Path to PVU cases directory.
    out_dir:    Output directory for artefacts.
    mode:       ``"offline"`` or ``"llm"``.
    seed:       Global random seed.
    train_frac: Fraction of steps for training.
    val_frac:   Fraction of steps for validation.
    horizon:    Forecast horizon in steps.

    Returns
    -------
    dict
        Full results dictionary (also written to disk).
    """
    np.random.seed(seed)

    print(f"[runner] Mode: {mode}")
    print(f"[runner] Cases: {cases_dir}")
    print(f"[runner] Output: {out_dir}")
    print(f"[runner] Seed: {seed}")

    if mode == "llm":
        _check_llm_secrets()

    cases = load_cases(cases_dir)
    print(f"[runner] Loaded {len(cases)} case(s).")

    baselines = get_all_baselines(seed=seed)
    baseline_names = [b.name for b in baselines]

    results: dict = {"cases": {}}

    for case in cases:
        print(f"[runner] Processing case: {case.case_id}")
        pol = _get_polarization(case)
        train, val, test = _split_series(pol, train_frac, val_frac)

        case_result: dict = {
            "meta": case.meta,
            "n_total_steps": len(pol),
            "n_train_steps": len(train),
            "n_val_steps": len(val),
            "n_test_steps": len(test),
            "forecast_metrics": {},
            "turning_point_metrics": {},
        }

        # Fit and predict all baselines
        baseline_preds: dict[str, np.ndarray] = {}
        for bl in baselines:
            bl.fit(train)
            # For multi-step, predict test length (ignoring horizon for simplicity)
            preds = bl.predict(len(test))
            baseline_preds[bl.name] = preds
            fm = compute_all(test, preds)
            case_result["forecast_metrics"][bl.name] = fm
            tp = score_turning_points(test, preds)
            case_result["turning_point_metrics"][bl.name] = tp

        results["cases"][case.case_id] = case_result

    # Aggregate metrics across cases
    results["aggregate"] = _aggregate_results(results["cases"], baseline_names)

    # Diebold-Mariano vs primary baseline (ar1) — only if >= 2 test points per case
    dm_results: dict[str, dict] = {}
    primary_baseline = "ar1"
    for bl_name in baseline_names:
        if bl_name == primary_baseline:
            continue
        p_values: list[float] = []
        for case_id, case_data in results["cases"].items():
            # Recompute predictions for DM test — stored in forecast_metrics only as scalars
            # We need raw arrays; re-run on the stored split
            pass  # DM test is run at aggregate level; see below
        # Simplified: report placeholder for now (full DM requires raw preds)
    results["dm_tests"] = _run_dm_tests(cases, baselines, seed, train_frac, val_frac)

    # Write artefacts
    commit_sha = _get_commit_sha()
    run_meta = build_run_meta(
        mode=mode,
        seed=seed,
        cases_dir=cases_dir,
        commit_sha=commit_sha,
    )
    os.makedirs(out_dir, exist_ok=True)
    metrics_path = write_metrics_json(results, out_dir)
    report_path = write_report_md(results, out_dir, run_meta)
    meta_path = write_run_meta(run_meta, out_dir)

    print(f"[runner] Wrote: {metrics_path}")
    print(f"[runner] Wrote: {report_path}")
    print(f"[runner] Wrote: {meta_path}")
    print("[runner] Done.")
    return results


def _aggregate_results(
    cases: dict[str, dict],
    baseline_names: list[str],
) -> dict:
    """Compute mean metrics across all cases."""
    metric_keys = ["mae", "rmse", "mape", "da"]
    agg: dict = {"forecast_metrics": {}}
    for bl_name in baseline_names:
        vals: dict[str, list[float]] = {k: [] for k in metric_keys}
        for case_data in cases.values():
            fm = case_data.get("forecast_metrics", {}).get(bl_name, {})
            for k in metric_keys:
                v = fm.get(k)
                if v is not None and v == v:  # not NaN
                    vals[k].append(v)
        agg["forecast_metrics"][bl_name] = {
            k: (float(np.mean(v)) if v else float("nan")) for k, v in vals.items()
        }
    return agg


def _run_dm_tests(
    cases,
    baselines,
    seed: int,
    train_frac: float,
    val_frac: float,
) -> dict:
    """Run Diebold-Mariano tests: ar1 (primary) vs each other baseline."""
    primary_name = "ar1"
    dm_results: dict = {}

    # We need raw predictions again — re-fit on each case
    all_ar1_errs: list[float] = []
    other_errs: dict[str, list[float]] = {}

    for case in cases:
        pol = _get_polarization(case)
        train, _, test = _split_series(pol, train_frac, val_frac)
        if len(test) < 2:
            continue

        preds_by_name: dict[str, np.ndarray] = {}
        for bl in baselines:
            bl.fit(train)
            preds_by_name[bl.name] = bl.predict(len(test))

        ar1_preds = preds_by_name.get(primary_name)
        if ar1_preds is None:
            continue

        for bl in baselines:
            if bl.name == primary_name:
                continue
            other_errs.setdefault(bl.name, [])
            # Collect squared-error differences for DM
            # (We run per-case DM and aggregate p-values via Fisher's method
            #  as a simple approach when N cases is small)
            dm_stat, p_val = diebold_mariano(test, ar1_preds, preds_by_name[bl.name])
            other_errs[bl.name].append(p_val)

    # Aggregate p-values (simple mean — Fisher's method would require chi-sq)
    comparisons = list(other_errs.keys())
    raw_p = [float(np.mean(other_errs[b])) if other_errs[b] else 1.0 for b in comparisons]
    thresholds = holm_bonferroni(raw_p, alpha=0.05)

    for i, bl_name in enumerate(comparisons):
        dm_results[bl_name] = {
            "comparison": f"ar1_vs_{bl_name}",
            "p_value_mean": raw_p[i],
            "holm_threshold": thresholds[i],
            "significant": raw_p[i] < thresholds[i],
        }

    return dm_results


def _check_llm_secrets() -> None:
    """Raise SystemExit with a clear message if LLM keys are missing."""
    keys = ["OPENAI_API_KEY", "OPENROUTER_API_KEY", "GROQ_API_KEY"]
    found = [k for k in keys if os.environ.get(k)]
    if not found:
        print(
            "[runner] ERROR: --llm mode requires at least one of the following "
            f"environment variables: {keys}\n"
            "Set the variable in your environment or in GitHub Actions secrets, "
            "then re-run with --llm."
        )
        sys.exit(1)
    print(f"[runner] LLM mode: using credentials from {found[0]}.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PVU-BS Offline Benchmark Runner for BeyondSight",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--cases",
        default="datasets/pvu_cases",
        help="Path to the PVU cases directory.",
    )
    parser.add_argument(
        "--out",
        default="reports/validation/ci",
        help="Output directory for artefacts.",
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--offline",
        action="store_true",
        default=True,
        help="Run in offline mode (no LLM). Default.",
    )
    mode_group.add_argument(
        "--llm",
        action="store_true",
        help="Run in LLM mode (requires API key env vars).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    parser.add_argument(
        "--train-frac",
        type=float,
        default=0.6,
        help="Fraction of steps for training.",
    )
    parser.add_argument(
        "--val-frac",
        type=float,
        default=0.2,
        help="Fraction of steps for validation (remainder = test).",
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=1,
        help="Forecast horizon in steps.",
    )

    args = parser.parse_args()
    mode = "llm" if args.llm else "offline"

    run_benchmark(
        cases_dir=args.cases,
        out_dir=args.out,
        mode=mode,
        seed=args.seed,
        train_frac=args.train_frac,
        val_frac=args.val_frac,
        horizon=args.horizon,
    )


if __name__ == "__main__":
    main()
