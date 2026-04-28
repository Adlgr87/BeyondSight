# PVU-BS Pre-registration Template (EN)

> **Instructions:** Fill in every field BEFORE running any evaluation on the test set. Commit this file and record its SHA in `run_meta.json`. Any field left blank invalidates the pre-registration.

---

## 1. Identification

| Field | Value |
|---|---|
| Pre-registration ID | `preReg-<YYYYMMDD>-<initials>` |
| Date | YYYY-MM-DD |
| Author(s) | |
| Repository commit SHA | |
| `configs/pvu.yaml` SHA | |

---

## 2. Research Question

_State the specific hypothesis being tested. Example: "BeyondSight (offline, DeGroot-only) achieves lower MAE on P(t) than AR(1) across all 10 cases."_

---

## 3. Cases Included

List the `case_id` values included in this validation run:

- [ ] `case_id_1`
- [ ] `case_id_2`
- …

**Total N =** ___  
**Are all cases independent?** Yes / No (if No, list `cluster_id` groups)

---

## 4. Target Variable

- Primary variable: `polarization` (P(t))
- Forecast horizon h: ___ steps
- Turning-point parameters: δ_min = ___, gap_min = ___, τ = ___

---

## 5. Train / Val / Test Split

| Split | Proportion | Row indices |
|---|---|---|
| Train | | |
| Validation | | |
| Test | | |

Splitting strategy: _(chronological / blocked / other)_

---

## 6. Baselines

List baselines to be compared:

- [ ] `naive`
- [ ] `moving_average` (window = ___)
- [ ] `ar1`
- [ ] `random_regime`
- [ ] `degroot_only`
- [ ] Other: ___

**Primary baseline** (for Holm–Bonferroni primary test): ___

---

## 7. Metrics

Primary: MAE  
Secondary: RMSE, MAPE, DA  
Turning-point: Precision, Recall, F1, Mean Temporal Error  
Statistical test: Diebold–Mariano + Holm–Bonferroni (α = 0.05)

---

## 8. Mode

- [ ] Offline (default, CI-compatible)
- [ ] LLM (requires API key — document provider and model version below)

LLM provider/model: ___  
Temperature: ___  

---

## 9. Reproducibility

| Parameter | Value |
|---|---|
| `PYTHONHASHSEED` | |
| `numpy` seed (from `configs/pvu.yaml`) | |
| Python version | |
| OS | |
| Runner version (git SHA) | |

---

## 10. Anti-Leakage Declaration

I confirm that:

- [ ] I have NOT inspected any metric or plot from the test set before completing this form.
- [ ] I have NOT adjusted any model parameter after seeing test-period data.
- [ ] The `configs/pvu.yaml` committed above will NOT be modified after this pre-registration.
- [ ] Cases were selected based on pre-defined criteria, NOT on expected outcomes.

**Signature / Handle:** ___  
**Date:** YYYY-MM-DD

---

## 11. Expected Outcome (Optional)

_Optional: write a directional prediction (e.g., "expect ΔMAE ≈ 0.03 in favor of BeyondSight"). This cannot be changed after submission._
