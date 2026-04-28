# PVU-BS Validation Report Template (EN)

> **Instructions:** Fill in after completing the full validation run. Attach or link to `metrics.json` and `report.md`. Archive under `reports/validation/<run_id>/`.

---

## 1. Identification

| Field | Value |
|---|---|
| Report ID | `report-<run_id>` |
| Pre-registration ID | |
| Date of run | YYYY-MM-DD |
| Author(s) | |
| Repository commit SHA | |
| Runner output path | `reports/validation/<run_id>/` |

---

## 2. Mode and Configuration

- Mode: ☐ Offline ☐ LLM
- `configs/pvu.yaml` SHA: ___
- LLM provider/model (if LLM mode): ___
- `PYTHONHASHSEED`: ___
- `numpy` seed: ___

---

## 3. Cases Summary

| Case ID | Domain | N_steps | Split train/val/test | Independent? |
|---|---|---|---|---|
| | | | | |
| | | | | |

Total cases: ___  
Cases meeting independence criteria: ___

---

## 4. Results — P(t) Forecast

| Model | MAE | RMSE | MAPE | DA |
|---|---|---|---|---|
| BeyondSight | | | | |
| naive | | | | |
| moving_average | | | | |
| ar1 | | | | |
| random_regime | | | | |
| degroot_only | | | | |

_Aggregate across all cases (mean ± std)._

---

## 5. Results — Turning-Point Skill

| Model | Precision | Recall | F1 | Mean Temporal Error |
|---|---|---|---|---|
| BeyondSight | | | | |
| naive | | | | |
| ar1 | | | | |

---

## 6. Statistical Tests

| Comparison | DM statistic | p-value (raw) | p-value (Holm-adj) | Reject H₀? |
|---|---|---|---|---|
| BeyondSight vs. naive | | | | |
| BeyondSight vs. moving_average | | | | |
| BeyondSight vs. ar1 | | | | |
| BeyondSight vs. random_regime | | | | |
| BeyondSight vs. degroot_only | | | | |

FDR (BH) q-values: _(attach or link)_

---

## 7. Validation Level Reached

- [ ] 🥉 Bronze — Passes §8.1 of PVU-BS on ≥ 10 cases, offline mode
- [ ] 🥈 Silver — Bronze + LLM mode passes + TPS F1 > 0.5
- [ ] 🥇 Gold — Silver + independent external replication
- [ ] ❌ Not passed — describe reason:

---

## 8. Anomalies and Deviations

_List any deviations from the pre-registration, data quality issues, or caveats._

---

## 9. Conclusions

_Brief narrative summary of findings (3–5 sentences)._

---

## 10. Artefacts

- [ ] `metrics.json` attached / linked
- [ ] `report.md` attached / linked
- [ ] `run_meta.json` attached / linked
- [ ] Pre-registration document linked / SHA recorded

---

## 11. Sign-off

| Role | Name | Date |
|---|---|---|
| Runner | | |
| Reviewer | | |
