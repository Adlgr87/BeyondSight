# BeyondSight — Paquete de Validación Reproducible (PVU-BS) (ES)

**Versión:** 1.0  
**Estado:** Activo  
**Alcance:** Simulador híbrido BeyondSight — Índice de Polarización + Habilidad en Puntos de Inflexión  

---

## 1. Propósito y Alcance

El protocolo PVU-BS define el estándar mínimo de evidencia que BeyondSight debe cumplir antes de publicar cualquier afirmación científica sobre superioridad predictiva. Está diseñado para ser:

- **Falsable:** BeyondSight debe superar a los baselines, no solo "producir salidas."
- **Reproducible:** Todas las semillas, configuraciones y divisiones de datos están congeladas antes de ejecutar cualquier test.
- **Auditable:** Cualquier tercero puede re-ejecutar el benchmark únicamente con los artefactos.
- **Compatible con CI:** El modo offline funciona sin claves de API ni servicios externos.

---

## 2. Variables Objetivo

BeyondSight se valida sobre un **objetivo compuesto** que captura lo que lo hace valioso frente a predictores estándar de series temporales:

### 2.1 Índice de Polarización P(t)

En cada paso temporal *t*, el sistema predice el **Índice de Polarización** agregado:

```
P(t) = Masa en extremos = fracción de agentes con |opinión| > θ_ext
```

donde `θ_ext = 0.6` por defecto (configurable por caso). Se calcula desde la columna `polarization` de `timeseries.csv` (o se deriva de `opinion_mean` + `opinion_std` cuando ambas están presentes).

**Por qué:** Los predictores estándar AR(1) / naïve funcionan bien en medias de opinión suaves, pero fallan cuando los cambios de régimen crean bimodalidad — exactamente donde BeyondSight debe sobresalir.

### 2.2 Habilidad en Puntos de Inflexión (TPS)

Un **punto de inflexión** es un máximo o mínimo local de P(t) con amplitud ≥ `δ_min` (por defecto: 0.05) y separación temporal ≥ `gap_min` (por defecto: 3 pasos). El modelo se evalúa en:

- **Precisión / Recall / F1** de los puntos de inflexión detectados (dentro de una ventana de tolerancia `τ`, por defecto: 2 pasos).
- **Error Temporal Medio:** `|t_pred − t_true|` promediado sobre los eventos emparejados.

**Por qué:** Predecir *cuándo* ocurre un punto de inflexión es directamente accionable para decisores.

---

## 3. Casos Independientes — Definición Formal

Un **caso** es la tupla `(red, serie_temporal, intervenciones, meta)` almacenada en `datasets/pvu_cases/<case_id>/`.

Un caso se considera **independiente** de los demás si y solo si:

1. **Sin solapamiento de red:** Los conjuntos de nodos comparten < 5% de identificadores (tras anonimización), O el caso documenta que el solapamiento se modela mediante un `cluster_id` compartido.
2. **Sin solapamiento temporal:** Las ventanas de observación primarias no coinciden con un choque externo no modelado en ambos casos (o ambos comparten el mismo `shock_tag` y se agrupan en el mismo clúster).
3. **Procedencia de datos:** El campo `source` en `meta.json` es único por caso, o es la misma fuente con `community_id` disjuntos.

Los casos que comparten `cluster_id` se evalúan conjuntamente con estadísticas robustas a clústeres (véase §6.2).

---

## 4. Reglas Anti-Leakage

Las siguientes acciones constituyen **filtración del conjunto de test** e invalidan la ejecución de validación:

1. Inspeccionar cualquier métrica, gráfico o estadística agregada derivada de filas del test antes de congelar la configuración.
2. Ajustar prompts, temperatura, proveedor o modelo del LLM tras observar predicciones de test.
3. Seleccionar qué casos incluir en la evaluación final en base a los resultados.
4. Re-dividir train/val/test tras observar resultados.
5. Usar información de eventos del período de test de `interventions.json` como features sin haberlos declarado previamente en el pre-registro.

**Congelamiento de configuración:** El archivo `configs/pvu.yaml` (o el argumento `--config` equivalente) debe estar comprometido y su SHA registrado en el documento de pre-registro *antes* de cualquier evaluación sobre el conjunto de test.

---

## 5. Requisitos de Dataset

### 5.1 Mínimo para validación científica

| Criterio | Mínimo |
|---|---|
| Casos independientes (N) | ≥ 10 |
| Pasos por caso (ventana de test) | ≥ 20 |
| Dominios | ≥ 2 dominios distintos |
| Idiomas / regiones | ≥ 2 |

### 5.2 Casos de ejemplo (solo para CI)

El repositorio incluye 3 casos sintéticos de ejemplo (`sample_case_001–003`) para pruebas del pipeline de CI. Estos casos **no satisfacen** el requisito N ≥ 10. Existen únicamente para garantizar que el runner carga, calcula y produce resultados correctamente.

### 5.3 Formato de archivos

Véase [`pvu_case_spec_ES.md`](pvu_case_spec_ES.md) para el esquema completo.

---

## 6. Suite de Baselines

Todos los baselines son deterministas, con semilla fija, e implementados en `benchmarks/baselines.py`.

| Baseline | Descripción |
|---|---|
| `naive` | Repite el último valor observado (pronóstico de paseo aleatorio) |
| `moving_average` | Media móvil sobre una ventana configurable (por defecto: 5) |
| `ar1` | Modelo AR(1) ajustado por OLS en la división de entrenamiento |
| `random_regime` | Muestrea uniformemente una etiqueta de régimen; aplica su P histórico medio |
| `degroot_only` | Ejecuta el modelo DeGroot con calibración empírica, sin selector LLM |

---

## 7. Métricas

Calculadas en `benchmarks/metrics.py`:

| Métrica | Símbolo | Notas |
|---|---|---|
| Error Absoluto Medio | MAE | Métrica primaria para el pronóstico de P(t) |
| Raíz del Error Cuadrático Medio | RMSE | Métrica secundaria |
| Error Porcentual Absoluto Medio | MAPE | Robusto a valores cercanos a cero: omitir si \|y\| < ε |
| Precisión Direccional | DA | Fracción de pasos con signo correcto de ΔP |
| Cobertura de Intervalos | IC | Opcional; requiere intervalos de predicción |

Métricas de puntos de inflexión (en `benchmarks/turning_points.py`): Precisión, Recall, F1, Error Temporal Medio.

---

## 8. Criterio Estadístico

### 8.1 Criterio principal (para insignias Bronce / Plata / Oro)

BeyondSight **pasa** un nivel de validación si:

1. **vs. baseline principal (AR(1) o naïve):** Prueba de Diebold–Mariano, unilateral, `p_adj < 0.05` tras corrección Holm–Bonferroni sobre todos los baselines.
2. **Tamaño del efecto:** ΔMAE > 0 y ΔRMSE > 0 (BeyondSight es mejor en términos absolutos).
3. **No-inferioridad vs. baselines restantes:** ΔMAE ≥ −0.02 (BeyondSight no es más de 2 pp peor que ningún otro baseline).

### 8.2 Corrección por comparaciones múltiples

Con M baselines, se ejecutan M pruebas de Diebold–Mariano y se aplica la corrección **Holm–Bonferroni**:

1. Ordenar p-valores: p_(1) ≤ p_(2) ≤ … ≤ p_(M).
2. Umbral ajustado para la prueba k: α / (M − k + 1).
3. Rechazar H₀ (BeyondSight ≡ baseline) para la prueba k si p_(k) < α / (M − k + 1).

FDR (Benjamini–Hochberg) también se reporta como estadística secundaria.

### 8.3 Niveles de validación

| Nivel | Criterio |
|---|---|
| 🥉 Bronce | Pasa §8.1 en ≥ 10 casos, solo modo offline |
| 🥈 Plata | Bronce + modo LLM pasa §8.1 + TPS F1 > 0.5 |
| 🥇 Oro | Plata + replicación externa independiente |

---

## 9. Modos

| Modo | Flag CLI | Requiere LLM | Corre en CI |
|---|---|---|---|
| Offline | `--offline` | No | Sí (por defecto) |
| LLM | `--llm` | Sí (clave API) | Solo con secrets |

En modo offline, `degroot_only` reemplaza cualquier selección de régimen asistida por LLM. Los resultados son completamente deterministas dada una semilla fija.

---

## 10. Requisitos de Reproducibilidad

Antes de cada ejecución, registrar:

- SHA del commit Git del repositorio.
- Valor de `PYTHONHASHSEED` (establecido en `0` en CI).
- Semilla aleatoria de `numpy` (establecida en `configs/pvu.yaml`, clave `seed`).
- Versión de Python y sistema operativo.
- Proveedor + versión del modelo (solo modo LLM).
- Contenido completo de `configs/pvu.yaml`.

Todo lo anterior se escribe automáticamente en `reports/validation/<run_id>/run_meta.json` por el runner.

---

## 11. Artefactos de Salida

Cada ejecución produce bajo `reports/validation/<run_id>/`:

```
run_meta.json       # semilla, commit, hash de configuración, timestamp
metrics.json        # métricas por caso y agregadas para todos los baselines + BeyondSight
report.md           # resumen legible con veredicto de aprobado/reprobado
```

---

## 12. Historial de Cambios

| Fecha | Versión | Cambio |
|---|---|---|
| 2024-01 | 0.1 | Borrador inicial |
| 2025-04 | 1.0 | Listo para repo: anti-leakage, Holm-Bonferroni, modos offline/llm, objetivo compuesto |
