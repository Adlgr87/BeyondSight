# PVU-BS Case File Specification (EN)

**Version:** 1.0

Each PVU-BS case is a directory under `datasets/pvu_cases/<case_id>/` containing four mandatory files.

---

## Directory Structure

```
datasets/pvu_cases/
└── <case_id>/
    ├── meta.json           # Case metadata
    ├── timeseries.csv      # Opinion dynamics time series
    ├── interventions.json  # External events / shocks
    └── network.csv         # Aggregated interaction network
```

---

## 1. `meta.json`

```json
{
  "case_id": "string (unique, snake_case)",
  "description": "string",
  "source": "string (e.g. 'synthetic', 'reddit/r/politics', 'wikipedia/climate')",
  "community_id": "string (identifies the community within the source)",
  "cluster_id": "string or null (group overlapping cases; null if fully independent)",
  "shock_tag": "string or null",
  "domain": "string (e.g. 'politics', 'finance', 'health')",
  "language": "string (ISO 639-1, e.g. 'en', 'es')",
  "date_range": ["YYYY-MM-DD", "YYYY-MM-DD"],
  "granularity": "string ('daily', 'weekly', 'hourly')",
  "n_agents_proxy": "integer or null",
  "opinion_range": "string ('bipolar' for [-1,1] or 'probabilistic' for [0,1])",
  "license": "string",
  "is_synthetic": "boolean",
  "notes": "string or null"
}
```

**Required fields:** `case_id`, `description`, `source`, `domain`, `language`, `date_range`, `granularity`, `opinion_range`, `license`, `is_synthetic`.

---

## 2. `timeseries.csv`

Comma-separated, UTF-8, with header row.

**Required columns:**

| Column | Type | Description |
|---|---|---|
| `t` | integer | Time step index (0-based) |
| `date` | string (YYYY-MM-DD) | Calendar date |
| `polarization` | float [0,1] | Primary target variable P(t) |

**Optional columns (enhance metrics):**

| Column | Type | Description |
|---|---|---|
| `opinion_mean` | float | Mean opinion across agents |
| `opinion_std` | float | Standard deviation of opinions |
| `volume` | integer | Number of observations / posts |
| `sentiment_mean` | float | External sentiment signal |
| `toxicity_proxy` | float [0,1] | Proxy for toxicity/hostility level |

All floating-point values must be valid IEEE 754 (no `NaN` in required columns). Use empty string for optional missing values.

---

## 3. `interventions.json`

A JSON array of intervention / shock objects.

```json
[
  {
    "t": 10,
    "date": "YYYY-MM-DD",
    "label": "string (short event name)",
    "type": "string ('policy', 'media', 'election', 'synthetic', ...)",
    "magnitude": 0.3,
    "description": "string"
  }
]
```

`magnitude` is optional (float in [0, 1]). Empty array `[]` is valid if there are no known events.

---

## 4. `network.csv`

Aggregated interaction network, comma-separated, UTF-8, with header row.

```csv
node_a,node_b,weight,period
user_hash_0001,user_hash_0002,12,all
```

**Required columns:** `node_a`, `node_b`, `weight`.  
**Optional column:** `period` (e.g. `"train"`, `"test"`, `"all"`).

Node identifiers must be anonymised (hashed). The network represents aggregate interaction intensity (e.g. reply count, co-occurrence) and should **not** contain personally identifiable information.

For very small synthetic cases, a minimal 3–5 node network is acceptable.

---

## 5. Validation Rules

The runner (`benchmarks/io.py`) enforces:

1. All four files exist.
2. `meta.json` contains all required fields.
3. `timeseries.csv` has required columns and no NaN in `t`, `date`, or `polarization`.
4. `polarization` values are in [0, 1].
5. `interventions.json` is a valid JSON array.
6. `network.csv` has required columns.

Violations raise `ValueError` with a descriptive message.

---

## 6. Scientific vs. Sample Cases

| Property | Scientific case | Sample / CI case |
|---|---|---|
| `is_synthetic` | false | true |
| Minimum steps | ≥ 100 (recommended) | Any (≥ 30 for CI) |
| Network | Real interaction data | Synthetic random graph |
| Counts toward N | Yes | **No** |
