# Plantilla de Reporte de Validación PVU-BS (ES)

> **Instrucciones:** Completar después de finalizar la corrida de validación completa. Adjuntar o enlazar `metrics.json` y `report.md`. Archivar en `reports/validation/<run_id>/`.

---

## 1. Identificación

| Campo | Valor |
|---|---|
| ID del reporte | `report-<run_id>` |
| ID de pre-registro | |
| Fecha de ejecución | YYYY-MM-DD |
| Autor(es) | |
| SHA del commit del repositorio | |
| Ruta de salida del runner | `reports/validation/<run_id>/` |

---

## 2. Modo y Configuración

- Modo: ☐ Offline ☐ LLM
- SHA de `configs/pvu.yaml`: ___
- Proveedor/modelo LLM (si modo LLM): ___
- `PYTHONHASHSEED`: ___
- Semilla de `numpy`: ___

---

## 3. Resumen de Casos

| Case ID | Dominio | N_pasos | División train/val/test | ¿Independiente? |
|---|---|---|---|---|
| | | | | |
| | | | | |

Total de casos: ___  
Casos que cumplen criterios de independencia: ___

---

## 4. Resultados — Pronóstico de P(t)

| Modelo | MAE | RMSE | MAPE | DA |
|---|---|---|---|---|
| BeyondSight | | | | |
| naive | | | | |
| moving_average | | | | |
| ar1 | | | | |
| random_regime | | | | |
| degroot_only | | | | |

_Agregado sobre todos los casos (media ± desv. estándar)._

---

## 5. Resultados — Habilidad en Puntos de Inflexión

| Modelo | Precisión | Recall | F1 | Error Temporal Medio |
|---|---|---|---|---|
| BeyondSight | | | | |
| naive | | | | |
| ar1 | | | | |

---

## 6. Pruebas Estadísticas

| Comparación | Estadístico DM | p-valor (raw) | p-valor (Holm-adj) | ¿Rechaza H₀? |
|---|---|---|---|---|
| BeyondSight vs. naive | | | | |
| BeyondSight vs. moving_average | | | | |
| BeyondSight vs. ar1 | | | | |
| BeyondSight vs. random_regime | | | | |
| BeyondSight vs. degroot_only | | | | |

Valores q FDR (BH): _(adjuntar o enlazar)_

---

## 7. Nivel de Validación Alcanzado

- [ ] 🥉 Bronce — Pasa §8.1 del PVU-BS en ≥ 10 casos, modo offline
- [ ] 🥈 Plata — Bronce + modo LLM pasa + TPS F1 > 0.5
- [ ] 🥇 Oro — Plata + replicación externa independiente
- [ ] ❌ No aprobado — describir razón:

---

## 8. Anomalías y Desviaciones

_Listar cualquier desviación del pre-registro, problemas de calidad de datos o advertencias._

---

## 9. Conclusiones

_Breve resumen narrativo de los hallazgos (3–5 oraciones)._

---

## 10. Artefactos

- [ ] `metrics.json` adjunto / enlazado
- [ ] `report.md` adjunto / enlazado
- [ ] `run_meta.json` adjunto / enlazado
- [ ] Documento de pre-registro enlazado / SHA registrado

---

## 11. Firmas

| Rol | Nombre | Fecha |
|---|---|---|
| Ejecutor | | |
| Revisor | | |
