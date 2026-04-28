"""
benchmarks/report.py — Generate report.md and metrics.json from benchmark results.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any


def _fmt(v: Any, decimals: int = 4) -> str:
    if isinstance(v, float):
        if v != v:  # NaN check
            return "N/A"
        return f"{v:.{decimals}f}"
    return str(v)


def write_metrics_json(results: dict[str, Any], out_dir: str) -> str:
    """Write results to ``metrics.json`` in *out_dir*. Returns the file path."""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "metrics.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, default=str)
    return path


def write_report_md(results: dict[str, Any], out_dir: str, run_meta: dict[str, Any]) -> str:
    """Write a human-readable ``report.md`` to *out_dir*. Returns the file path."""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "report.md")

    lines: list[str] = []
    lines.append("# PVU-BS Validation Report\n")
    lines.append(f"**Generated:** {run_meta.get('timestamp', 'N/A')}  ")
    lines.append(f"**Mode:** {run_meta.get('mode', 'N/A')}  ")
    lines.append(f"**Seed:** {run_meta.get('seed', 'N/A')}  ")
    lines.append(f"**Commit:** `{run_meta.get('commit_sha', 'N/A')}`  ")
    lines.append(f"**Cases dir:** `{run_meta.get('cases_dir', 'N/A')}`  \n")

    cases_results = results.get("cases", {})
    aggregate = results.get("aggregate", {})

    lines.append(f"## Cases Summary\n")
    lines.append(f"Total cases loaded: **{len(cases_results)}**  \n")

    for case_id, case_data in cases_results.items():
        lines.append(f"### Case: `{case_id}`\n")
        meta = case_data.get("meta", {})
        lines.append(f"- Domain: {meta.get('domain', 'N/A')}  ")
        lines.append(f"- Source: {meta.get('source', 'N/A')}  ")
        lines.append(f"- Synthetic: {meta.get('is_synthetic', '?')}  ")
        lines.append(f"- Steps (test): {case_data.get('n_test_steps', '?')}  \n")

        forecast_metrics = case_data.get("forecast_metrics", {})
        if forecast_metrics:
            lines.append("#### Forecast Metrics (P(t) — test set)\n")
            lines.append("| Model | MAE | RMSE | MAPE | DA |")
            lines.append("|---|---|---|---|---|")
            for model, m in forecast_metrics.items():
                lines.append(
                    f"| {model} "
                    f"| {_fmt(m.get('mae'))} "
                    f"| {_fmt(m.get('rmse'))} "
                    f"| {_fmt(m.get('mape'))} "
                    f"| {_fmt(m.get('da'))} |"
                )
            lines.append("")

        tp_metrics = case_data.get("turning_point_metrics", {})
        if tp_metrics:
            lines.append("#### Turning-Point Metrics\n")
            lines.append("| Model | Precision | Recall | F1 | Mean Temporal Error |")
            lines.append("|---|---|---|---|---|")
            for model, m in tp_metrics.items():
                lines.append(
                    f"| {model} "
                    f"| {_fmt(m.get('precision'))} "
                    f"| {_fmt(m.get('recall'))} "
                    f"| {_fmt(m.get('f1'))} "
                    f"| {_fmt(m.get('mean_temporal_error'))} |"
                )
            lines.append("")

    if aggregate:
        lines.append("## Aggregate Results (mean across cases)\n")
        lines.append("| Model | MAE | RMSE | MAPE | DA |")
        lines.append("|---|---|---|---|---|")
        for model, m in aggregate.get("forecast_metrics", {}).items():
            lines.append(
                f"| {model} "
                f"| {_fmt(m.get('mae'))} "
                f"| {_fmt(m.get('rmse'))} "
                f"| {_fmt(m.get('mape'))} "
                f"| {_fmt(m.get('da'))} |"
            )
        lines.append("")

    lines.append("## Notes\n")
    lines.append(
        "> ⚠️ Sample cases are **synthetic** and do not constitute scientific validation evidence.  \n"
        "> See `docs/validation/PVU_BeyondSight_EN.md` for the full protocol requirements (N ≥ 10 real cases).\n"
    )

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return path


def write_run_meta(run_meta: dict[str, Any], out_dir: str) -> str:
    """Write ``run_meta.json`` to *out_dir*. Returns the file path."""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "run_meta.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(run_meta, fh, indent=2, default=str)
    return path


def build_run_meta(
    mode: str,
    seed: int,
    cases_dir: str,
    commit_sha: str = "unknown",
) -> dict[str, Any]:
    """Build the run metadata dictionary."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "seed": seed,
        "cases_dir": cases_dir,
        "commit_sha": commit_sha,
        "python_hashseed": os.environ.get("PYTHONHASHSEED", "not_set"),
    }
