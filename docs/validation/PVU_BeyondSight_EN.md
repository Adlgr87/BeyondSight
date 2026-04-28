# BeyondSight Reproducible Validation Package — PVU-BS (EN)

**Version:** 1.0  
**Status:** Active  
**Scope:** BeyondSight hybrid simulator — Polarization Index + Turning-Point Skill  

---

## 1. Purpose and Scope

The PVU-BS protocol defines the minimum evidentiary standard that BeyondSight must meet before any scientific claim about predictive superiority is made public. It is designed to be:

- **Falsifiable:** BeyondSight must outperform baselines, not just "produce outputs."
- **Reproducible:** All seeds, configurations, and data splits are frozen before any test is run.
- **Auditable:** Any third party can re-run the benchmark from the artefacts alone.
- **CI-friendly:** The offline mode runs without API keys or external services.

---

## 2. Target Variables

BeyondSight is validated on a **composite objective** that captures what makes it uniquely valuable relative to standard time-series forecasters:

### 2.1 Polarization Index P(t)

At each time step *t*, the system predicts the aggregate **Polarization Index**:

```
P(t) = Mass at extremes = fraction of agents with |opinion| > θ_ext
```

where `θ_ext = 0.6` by default (configurable per case). This is computed from `timeseries.csv` column `polarization` (or derived from `opinion_mean` + `opinion_std` when both are present).

**Why:** Standard AR(1) / naïve forecasters perform well on smooth opinion means but fail when regime changes create bimodality — exactly where BeyondSight should excel.

### 2.2 Turning-Point Skill (TPS)

A **turning point** is a local maximum or minimum in P(t) with amplitude ≥ `δ_min` (default: 0.05) and temporal separation ≥ `gap_min` (default: 3 steps). The model is evaluated on:

- **Precision / Recall / F1** of detected turning points (within a tolerance window `τ`, default: 2 steps).
- **Mean Temporal Error:** `|t_pred − t_true|` averaged over matched events.

**Why:** Predicting *when* a tipping point occurs is directly actionable for decision-makers.

---

## 3. Independent Cases — Formal Definition

A **case** is the tuple `(network, timeseries, interventions, meta)` stored under `datasets/pvu_cases/<case_id>/`.

A case is considered **independent** of others if and only if:

1. **Network non-overlap:** The node sets share < 5% of identifiers (after anonymisation), OR the case documents that overlap is modelled via a shared `cluster_id`.
2. **Temporal non-overlap:** The primary observation windows do not coincide with an external shock that is unmodelled in both cases (or both cases share the same `shock_tag` and are grouped into the same cluster).
3. **Data provenance:** The `meta.json` field `source` is unique per case, or is the same source with disjoint `community_id`.

Cases that share a `cluster_id` are evaluated together using cluster-robust statistics (see §6.2).

---

## 4. Anti-Leakage Rules

The following actions constitute **test-set leakage** and invalidate the validation run:

1. Inspecting any metric, plot, or aggregated statistic derived from test-set rows before the configuration is frozen.
2. Adjusting LLM prompts, temperature, provider, or model after observing test predictions.
3. Selecting which cases to include in the final evaluation based on results.
4. Re-splitting train/val/test after observing outcomes.
5. Using information from `interventions.json` test-period events as features without pre-declaring them in the pre-registration.

**Configuration freeze:** The file `configs/pvu.yaml` (or the equivalent `--config` argument) must be committed and its SHA recorded in the pre-registration document *before* any test-set evaluation.

---

## 5. Dataset Requirements

### 5.1 Minimum for scientific validation

| Criterion | Minimum |
|---|---|
| Independent cases (N) | ≥ 10 |
| Steps per case (test window) | ≥ 20 |
| Domains | ≥ 2 distinct domains |
| Languages / regions | ≥ 2 |

### 5.2 Sample cases (CI only)

The repository includes 3 synthetic sample cases (`sample_case_001–003`) for CI pipeline testing. These cases **do not satisfy** the N ≥ 10 requirement. They exist solely to ensure the runner loads, computes, and outputs results correctly.

### 5.3 File format

See [`pvu_case_spec_EN.md`](pvu_case_spec_EN.md) for the full schema.

---

## 6. Baseline Suite

All baselines are deterministic, seed-fixed, and implemented in `benchmarks/baselines.py`.

| Baseline | Description |
|---|---|
| `naive` | Repeat last observed value (random-walk forecast) |
| `moving_average` | Rolling mean over a configurable window (default: 5) |
| `ar1` | AR(1) model fitted via OLS on the training split |
| `random_regime` | Uniformly sample a regime label; apply its mean historical P |
| `degroot_only` | Run DeGroot model with empirical calibration, no LLM selector |

---

## 7. Metrics

Computed in `benchmarks/metrics.py`:

| Metric | Symbol | Notes |
|---|---|---|
| Mean Absolute Error | MAE | Primary metric for P(t) forecast |
| Root Mean Squared Error | RMSE | Secondary metric |
| Mean Absolute Percentage Error | MAPE | Robust to near-zero: skip if \|y\| < ε |
| Directional Accuracy | DA | Fraction of steps with correct sign of ΔP |
| Interval Coverage | IC | Optional; requires prediction intervals |

Turning-point metrics (in `benchmarks/turning_points.py`): Precision, Recall, F1, Mean Temporal Error.

---

## 8. Statistical Criterion

### 8.1 Primary criterion (for Bronce / Silver / Gold badges)

BeyondSight **passes** a validation level if:

1. **vs. primary baseline (AR(1) or naïve):** Diebold–Mariano test, one-sided, `p_adj < 0.05` after Holm–Bonferroni correction across all baselines.
2. **Effect size:** ΔMAE > 0 and ΔRMSE > 0 (BeyondSight is better in absolute terms).
3. **Non-inferiority vs. remaining baselines:** ΔMAE ≥ −0.02 (BeyondSight is not more than 2 pp worse than any other baseline).

### 8.2 Multiple comparisons correction

With M baselines, run M Diebold–Mariano tests and apply **Holm–Bonferroni** correction:

1. Sort p-values: p_(1) ≤ p_(2) ≤ … ≤ p_(M).
2. Adjusted threshold for test k: α / (M − k + 1).
3. Reject H₀ (BeyondSight ≡ baseline) for test k if p_(k) < α / (M − k + 1).

FDR (Benjamini–Hochberg) is also reported as a secondary statistic.

### 8.3 Validation levels

| Level | Criterion |
|---|---|
| 🥉 Bronze | Passes §8.1 on ≥ 10 cases, offline mode only |
| 🥈 Silver | Bronze + LLM mode passes §8.1 + TPS F1 > 0.5 |
| 🥇 Gold | Silver + independent external replication |

---

## 9. Modes

| Mode | CLI flag | LLM required | Runs in CI |
|---|---|---|---|
| Offline | `--offline` | No | Yes (default) |
| LLM | `--llm` | Yes (API key) | Only with secrets |

In offline mode, `degroot_only` replaces any LLM-assisted regime selection. Results are fully deterministic given a fixed seed.

---

## 10. Reproducibility Requirements

Before each run, record:

- Git commit SHA of the repository.
- `PYTHONHASHSEED` value (set to `0` in CI).
- `numpy` random seed (set in `configs/pvu.yaml`, key `seed`).
- Python version and OS.
- Model provider + version (LLM mode only).
- Full content of `configs/pvu.yaml`.

All of the above are written automatically to `reports/validation/<run_id>/run_meta.json` by the runner.

---

## 11. Output Artefacts

Each run produces under `reports/validation/<run_id>/`:

```
run_meta.json       # seed, commit, config hash, timestamp
metrics.json        # per-case and aggregate metrics for all baselines + BeyondSight
report.md           # human-readable summary with pass/fail verdict
```

---

## 12. Changelog

| Date | Version | Change |
|---|---|---|
| 2024-01 | 0.1 | Initial draft |
| 2025-04 | 1.0 | Repo-ready: anti-leakage, Holm-Bonferroni, offline/llm modes, composite target |
