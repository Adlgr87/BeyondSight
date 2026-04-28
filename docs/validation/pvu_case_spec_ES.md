# Especificación de Archivos de Casos PVU-BS (ES)

**Versión:** 1.0

Cada caso PVU-BS es un directorio en `datasets/pvu_cases/<case_id>/` que contiene cuatro archivos obligatorios.

---

## Estructura de Directorio

```
datasets/pvu_cases/
└── <case_id>/
    ├── meta.json           # Metadatos del caso
    ├── timeseries.csv      # Serie temporal de dinámica de opiniones
    ├── interventions.json  # Eventos externos / choques
    └── network.csv         # Red de interacción agregada
```

---

## 1. `meta.json`

```json
{
  "case_id": "string (único, snake_case)",
  "description": "string",
  "source": "string (ej. 'synthetic', 'reddit/r/politics', 'wikipedia/climate')",
  "community_id": "string (identifica la comunidad dentro de la fuente)",
  "cluster_id": "string o null (agrupa casos solapados; null si es completamente independiente)",
  "shock_tag": "string o null",
  "domain": "string (ej. 'politics', 'finance', 'health')",
  "language": "string (ISO 639-1, ej. 'en', 'es')",
  "date_range": ["YYYY-MM-DD", "YYYY-MM-DD"],
  "granularity": "string ('daily', 'weekly', 'hourly')",
  "n_agents_proxy": "entero o null",
  "opinion_range": "string ('bipolar' para [-1,1] o 'probabilistic' para [0,1])",
  "license": "CC0",
  "is_synthetic": true,
  "notes": "string o null"
}
```

**Campos obligatorios:** `case_id`, `description`, `source`, `domain`, `language`, `date_range`, `granularity`, `opinion_range`, `license`, `is_synthetic`.

---

## 2. `timeseries.csv`

Separado por comas, UTF-8, con fila de encabezado.

**Columnas obligatorias:**

| Columna | Tipo | Descripción |
|---|---|---|
| `t` | entero | Índice de paso temporal (base 0) |
| `date` | string (YYYY-MM-DD) | Fecha de calendario |
| `polarization` | float [0,1] | Variable objetivo principal P(t) |

**Columnas opcionales (mejoran las métricas):**

| Columna | Tipo | Descripción |
|---|---|---|
| `opinion_mean` | float | Media de opinión entre agentes |
| `opinion_std` | float | Desviación estándar de opiniones |
| `volume` | entero | Número de observaciones / publicaciones |
| `sentiment_mean` | float | Señal externa de sentimiento |
| `toxicity_proxy` | float [0,1] | Proxy de nivel de toxicidad/hostilidad |

Todos los valores de punto flotante deben ser IEEE 754 válidos (sin `NaN` en columnas obligatorias). Usar cadena vacía para valores opcionales faltantes.

---

## 3. `interventions.json`

Un array JSON de objetos de intervención / choque.

```json
[
  {
    "t": 10,
    "date": "YYYY-MM-DD",
    "label": "string (nombre corto del evento)",
    "type": "string ('policy', 'media', 'election', 'synthetic', ...)",
    "magnitude": 0.3,
    "description": "string"
  }
]
```

`magnitude` es opcional (float en [0, 1]). El array vacío `[]` es válido si no hay eventos conocidos.

---

## 4. `network.csv`

Red de interacción agregada, separada por comas, UTF-8, con fila de encabezado.

```csv
node_a,node_b,weight,period
user_hash_0001,user_hash_0002,12,all
```

**Columnas obligatorias:** `node_a`, `node_b`, `weight`.  
**Columna opcional:** `period` (ej. `"train"`, `"test"`, `"all"`).

Los identificadores de nodos deben estar anonimizados (hash). La red representa intensidad de interacción agregada (ej. conteo de respuestas, co-ocurrencia) y **no** debe contener información de identificación personal.

Para casos sintéticos pequeños, una red mínima de 3–5 nodos es aceptable.

---

## 5. Reglas de Validación

El runner (`benchmarks/io.py`) verifica:

1. Los cuatro archivos existen.
2. `meta.json` contiene todos los campos obligatorios.
3. `timeseries.csv` tiene las columnas obligatorias y sin NaN en `t`, `date` o `polarization`.
4. Los valores de `polarization` están en [0, 1].
5. `interventions.json` es un array JSON válido.
6. `network.csv` tiene las columnas obligatorias.

Las violaciones lanzan `ValueError` con un mensaje descriptivo.

---

## 6. Casos Científicos vs. De Muestra

| Propiedad | Caso científico | Caso de muestra / CI |
|---|---|---|
| `is_synthetic` | false | true |
| Pasos mínimos | ≥ 100 (recomendado) | Cualquiera (≥ 30 para CI) |
| Red | Datos de interacción reales | Grafo aleatorio sintético |
| Cuenta para N | Sí | **No** |
