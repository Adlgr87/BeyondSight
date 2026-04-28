# Plantilla de Pre-registro PVU-BS (ES)

> **Instrucciones:** Completar cada campo ANTES de ejecutar cualquier evaluación en el conjunto de test. Commitear este archivo y registrar su SHA en `run_meta.json`. Cualquier campo en blanco invalida el pre-registro.

---

## 1. Identificación

| Campo | Valor |
|---|---|
| ID de pre-registro | `preReg-<YYYYMMDD>-<iniciales>` |
| Fecha | YYYY-MM-DD |
| Autor(es) | |
| SHA del commit del repositorio | |
| SHA de `configs/pvu.yaml` | |

---

## 2. Pregunta de Investigación

_Indicar la hipótesis específica que se va a probar. Ejemplo: "BeyondSight (offline, solo DeGroot) logra menor MAE en P(t) que AR(1) en los 10 casos."_

---

## 3. Casos Incluidos

Listar los valores de `case_id` incluidos en esta corrida de validación:

- [ ] `case_id_1`
- [ ] `case_id_2`
- …

**N total =** ___  
**¿Todos los casos son independientes?** Sí / No (si No, listar grupos de `cluster_id`)

---

## 4. Variable Objetivo

- Variable primaria: `polarization` (P(t))
- Horizonte de pronóstico h: ___ pasos
- Parámetros de puntos de inflexión: δ_min = ___, gap_min = ___, τ = ___

---

## 5. División Train / Val / Test

| División | Proporción | Índices de filas |
|---|---|---|
| Train | | |
| Validación | | |
| Test | | |

Estrategia de división: _(cronológica / bloques / otra)_

---

## 6. Baselines

Listar los baselines a comparar:

- [ ] `naive`
- [ ] `moving_average` (ventana = ___)
- [ ] `ar1`
- [ ] `random_regime`
- [ ] `degroot_only`
- [ ] Otro: ___

**Baseline principal** (para prueba primaria Holm–Bonferroni): ___

---

## 7. Métricas

Primaria: MAE  
Secundarias: RMSE, MAPE, DA  
Puntos de inflexión: Precisión, Recall, F1, Error Temporal Medio  
Prueba estadística: Diebold–Mariano + Holm–Bonferroni (α = 0.05)

---

## 8. Modo

- [ ] Offline (por defecto, compatible con CI)
- [ ] LLM (requiere clave de API — documentar proveedor y versión del modelo a continuación)

Proveedor/modelo LLM: ___  
Temperatura: ___  

---

## 9. Reproducibilidad

| Parámetro | Valor |
|---|---|
| `PYTHONHASHSEED` | |
| Semilla de `numpy` (de `configs/pvu.yaml`) | |
| Versión de Python | |
| Sistema operativo | |
| Versión del runner (SHA git) | |

---

## 10. Declaración Anti-Leakage

Confirmo que:

- [ ] NO he inspeccionado ninguna métrica o gráfico del conjunto de test antes de completar este formulario.
- [ ] NO he ajustado ningún parámetro del modelo tras ver datos del período de test.
- [ ] El `configs/pvu.yaml` comprometido arriba NO será modificado tras este pre-registro.
- [ ] Los casos fueron seleccionados en base a criterios pre-definidos, NO en base a resultados esperados.

**Firma / Handle:** ___  
**Fecha:** YYYY-MM-DD

---

## 11. Resultado Esperado (Opcional)

_Opcional: escribir una predicción direccional (ej. "se espera ΔMAE ≈ 0.03 a favor de BeyondSight"). No puede modificarse tras el envío._
