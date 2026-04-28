"""
BeyondSight — PVU Runner
========================
CLI entry-point for the Predictive Validation Unit (PVU) pipeline.

Usage
-----
Offline (CI / no API keys required):
    python -m benchmarks.runner --cases datasets/pvu_cases --offline --out reports/validation/ci

LLM-assisted (requires secrets):
    python -m benchmarks.runner --cases datasets/pvu_cases --llm --out reports/validation/ci

Each case directory must contain:
    timeseries.csv       — columns: date, polarization  (+ optional: volume, sentiment_mean)
    interventions.json   — list of {date, label, source}
    meta.json            — {id, domain, source, language, cluster_id, granularity, license}

The runner:
  1) Loads and validates every case.
  2) Splits each series into train / val / test (reproducible, no leakage).
  3) Fits all baselines on train, evaluates on test.
  4) Computes PVU metrics (MAE, RMSE, MAPE, DA, TP-F1, TP-timing-error).
  5) Writes metrics.json + report.md to --out directory.
  6) Exits 0 if the run completed without errors (gates are advisory, not blocking).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------

SEED = int(os.environ.get("PYTHONHASHSEED", "42"))
random.seed(SEED)


# ---------------------------------------------------------------------------
# Case I/O
# ---------------------------------------------------------------------------

def _load_timeseries(path: Path) -> list[dict]:
    """Load timeseries.csv and return list of row dicts."""
    rows: list[dict] = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append({k: v.strip() for k, v in row.items()})
    return rows


def _load_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_case(case_dir: Path) -> dict:
    """Load a single PVU case directory and return a structured dict."""
    ts_path = case_dir / "timeseries.csv"
    meta_path = case_dir / "meta.json"
    interv_path = case_dir / "interventions.json"

    if not ts_path.exists():
        raise FileNotFoundError(f"Missing timeseries.csv in {case_dir}")
    if not meta_path.exists():
        raise FileNotFoundError(f"Missing meta.json in {case_dir}")

    rows = _load_timeseries(ts_path)
    meta = _load_json(meta_path)
    interventions = _load_json(interv_path) if interv_path.exists() else []

    # Extract polarization series (float) — fallback to 'value' column
    pol_key = "polarization" if "polarization" in (rows[0] if rows else {}) else "value"
    series = [float(r[pol_key]) for r in rows]
    dates = [r.get("date", str(i)) for i, r in enumerate(rows)]

    return {
        "id": meta.get("id", case_dir.name),
        "meta": meta,
        "dates": dates,
        "series": series,
        "interventions": interventions,
    }


# ---------------------------------------------------------------------------
# Train / val / test split
# ---------------------------------------------------------------------------

def split_series(
    series: list[float],
    train_frac: float = 0.60,
    val_frac: float = 0.20,
) -> tuple[list[float], list[float], list[float]]:
    n = len(series)
    i_train = max(1, int(n * train_frac))
    i_val = max(i_train + 1, int(n * (train_frac + val_frac)))
    return series[:i_train], series[i_train:i_val], series[i_val:]


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate_case(case: dict, train_frac: float = 0.60, val_frac: float = 0.20) -> dict:
    """Fit all baselines on train and evaluate on test. Returns metrics dict."""
    from benchmarks.baselines import ALL_BASELINES
    from benchmarks.metrics import compute_all
    from benchmarks.turning_points import detect_turning_points

    series = case["series"]
    train, val, test = split_series(series, train_frac=train_frac, val_frac=val_frac)

    if len(test) < 2:
        return {"case_id": case["id"], "skipped": True, "reason": "test set too small"}

    true_tp_events = detect_turning_points(test)
    results: dict[str, dict] = {}

    for bl_name, bl_cls in ALL_BASELINES.items():
        bl = bl_cls()
        bl.fit(train)
        last_train_y = train[-1]
        preds = bl.predict(len(test), last_y=last_train_y)
        pred_tp_events = detect_turning_points(preds)
        m = compute_all(test, preds, true_events=true_tp_events, pred_events=pred_tp_events)
        results[bl_name] = m

    return {
        "case_id": case["id"],
        "n_total": len(series),
        "n_train": len(train),
        "n_val": len(val),
        "n_test": len(test),
        "metrics_by_baseline": results,
        "skipped": False,
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

_NAN_STR = "N/A"


def _fmt(v: float | str) -> str:
    if isinstance(v, str):
        return v
    if math.isnan(v) or math.isinf(v):
        return _NAN_STR
    return f"{v:.4f}"


def build_report(all_results: list[dict], mode: str, cases_path: str) -> str:
    """Generate a Markdown PVU validation report."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines: list[str] = [
        "# BeyondSight — PVU Validation Report",
        "",
        f"**Generated:** {ts}  ",
        f"**Mode:** {mode}  ",
        f"**Cases path:** `{cases_path}`  ",
        "",
        "---",
        "",
    ]

    skipped = [r for r in all_results if r.get("skipped")]
    evaluated = [r for r in all_results if not r.get("skipped")]

    lines.append(f"**Cases evaluated:** {len(evaluated)}  ")
    lines.append(f"**Cases skipped:** {len(skipped)}  ")
    lines.append("")

    for res in evaluated:
        lines.append(f"## Case: `{res['case_id']}`")
        lines.append(
            f"Split — train: {res['n_train']} | val: {res['n_val']} | test: {res['n_test']}"
        )
        lines.append("")
        lines.append(
            "| Baseline | MAE | RMSE | MAPE | Dir.Acc | TP-F1 | TP-Timing |"
        )
        lines.append(
            "|----------|-----|------|------|---------|-------|-----------|"
        )
        for bl, m in res["metrics_by_baseline"].items():
            row = (
                f"| {bl} "
                f"| {_fmt(m['mae'])} "
                f"| {_fmt(m['rmse'])} "
                f"| {_fmt(m['mape'])} "
                f"| {_fmt(m['directional_accuracy'])} "
                f"| {_fmt(m['turning_point_f1'])} "
                f"| {_fmt(m['turning_point_timing_error'])} |"
            )
            lines.append(row)
        lines.append("")

    for res in skipped:
        lines.append(f"## Case: `{res['case_id']}` — SKIPPED")
        lines.append(f"Reason: {res.get('reason', 'unknown')}")
        lines.append("")

    lines.append("---")
    lines.append("*BeyondSight PVU — offline runner*")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="BeyondSight PVU Validation Runner",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--cases", default="datasets/pvu_cases", help="Path to cases folder")
    parser.add_argument("--offline", action="store_true", help="Run in offline mode (no LLM)")
    parser.add_argument("--llm", action="store_true", help="Run in LLM-assisted mode")
    parser.add_argument("--out", default="reports/validation/ci", help="Output directory")
    parser.add_argument("--config", default="configs/pvu.yaml", help="YAML config file")
    parser.add_argument(
        "--train-frac", type=float, default=0.60, help="Train split fraction"
    )
    parser.add_argument(
        "--val-frac", type=float, default=0.20, help="Validation split fraction"
    )
    args = parser.parse_args(argv)

    mode = "llm" if args.llm and not args.offline else "offline"

    # LLM mode guard — skip gracefully when no API key is present
    if mode == "llm":
        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            print(
                "[PVU] LLM mode requested but no API key found "
                "(OPENAI_API_KEY / OPENROUTER_API_KEY). "
                "Falling back to offline mode.",
                file=sys.stderr,
            )
            mode = "offline"

    cases_path = Path(args.cases)
    out_path = Path(args.out)
    out_path.mkdir(parents=True, exist_ok=True)

    # Discover case directories
    if not cases_path.exists():
        print(f"[PVU] Cases path not found: {cases_path}", file=sys.stderr)
        return 1

    case_dirs = sorted(
        d for d in cases_path.iterdir() if d.is_dir() and not d.name.startswith(".")
    )

    if not case_dirs:
        print(f"[PVU] No case directories found in {cases_path}", file=sys.stderr)
        return 1

    print(f"[PVU] Mode: {mode} | Cases: {len(case_dirs)} | Output: {out_path}")

    all_results: list[dict] = []
    for case_dir in case_dirs:
        print(f"[PVU] Loading case: {case_dir.name} ...", end=" ", flush=True)
        try:
            case = load_case(case_dir)
            result = evaluate_case(case, train_frac=args.train_frac, val_frac=args.val_frac)
            all_results.append(result)
            if result.get("skipped"):
                print(f"SKIPPED ({result.get('reason')})")
            else:
                print("OK")
        except (FileNotFoundError, ValueError, KeyError, csv.Error) as exc:
            print(f"ERROR — {exc}")
            all_results.append(
                {"case_id": case_dir.name, "skipped": True, "reason": str(exc)}
            )

    # Write outputs
    metrics_path = out_path / "metrics.json"
    report_path = out_path / "report.md"

    with open(metrics_path, "w", encoding="utf-8") as fh:
        json.dump(all_results, fh, indent=2, default=str)

    report_md = build_report(all_results, mode=mode, cases_path=str(cases_path))
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(report_md)

    print(f"[PVU] Report written to {report_path}")
    print(f"[PVU] Metrics written to {metrics_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
