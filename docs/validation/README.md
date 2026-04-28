# Validation / Validación — PVU-BS

> **Bilingual index / Índice bilingüe**

---

## English

This section contains the **BeyondSight Reproducible Validation Package (PVU-BS)** — a formal protocol that defines how BeyondSight must be benchmarked against baselines before any scientific claim is made.

| Document | Description |
|---|---|
| [PVU Protocol (EN)](PVU_BeyondSight_EN.md) | Full validation protocol |
| [Case Specification (EN)](pvu_case_spec_EN.md) | Dataset schema & case format |
| [Pre-registration Template (EN)](preregistration_template_EN.md) | Fill before touching test data |
| [Validation Report Template (EN)](validation_report_template_EN.md) | Fill after completing a run |

### Running the offline benchmark locally

```bash
# Install dependencies (already in requirements.txt)
pip install -r requirements.txt

# Run PVU offline benchmark against sample cases
python -m benchmarks.runner --cases datasets/pvu_cases --offline --out reports/validation/local

# View results
cat reports/validation/local/report.md
```

---

## Español

Esta sección contiene el **Paquete de Validación Reproducible de BeyondSight (PVU-BS)** — un protocolo formal que define cómo BeyondSight debe compararse contra baselines antes de realizar cualquier afirmación científica.

| Documento | Descripción |
|---|---|
| [Protocolo PVU (ES)](PVU_BeyondSight_ES.md) | Protocolo completo de validación |
| [Especificación de Casos (ES)](pvu_case_spec_ES.md) | Esquema de datasets y formato de casos |
| [Plantilla de Pre-registro (ES)](preregistration_template_ES.md) | Completar antes de ver datos de test |
| [Plantilla de Reporte de Validación (ES)](validation_report_template_ES.md) | Completar tras finalizar una corrida |

### Ejecutar el benchmark offline localmente

```bash
# Instalar dependencias (ya en requirements.txt)
pip install -r requirements.txt

# Correr benchmark PVU offline con casos de ejemplo
python -m benchmarks.runner --cases datasets/pvu_cases --offline --out reports/validation/local

# Ver resultados
cat reports/validation/local/report.md
```

---

> ⚠️ **Note / Nota:** The sample cases in `datasets/pvu_cases/sample_case_00X/` are **synthetic** and exist solely to validate the CI pipeline. They do **not** constitute scientific validation evidence. See the protocol for requirements on real validation cases (N ≥ 10 independent cases).
>
> Los casos de ejemplo en `datasets/pvu_cases/sample_case_00X/` son **sintéticos** y existen únicamente para validar el pipeline de CI. **No** constituyen evidencia científica de validación. Véase el protocolo para los requisitos de casos reales (N ≥ 10 casos independientes).
