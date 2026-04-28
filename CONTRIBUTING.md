# Contributing to BeyondSight 🌊

First off, thank you for considering contributing to BeyondSight! It's people like you that make BeyondSight such a great tool for understanding and simulating social dynamics.

## 1. How you can help
We welcome contributions in various forms:
- **Mathematical Models:** Submitting new deterministic or stochastic rules for social cascades.
- **LLM Integrations:** Testing and providing support for new Large Language Model APIs via OpenRouter, Anthropic, etc.
- **Visuals:** Creating new algorithms for `visualizations.py` to support 3D interactions.
- **Bug Reporting & Docs:** Reporting issues and fixing typos or i18n bugs.

## 2. Setting up your environment
1. Fork the repo and clone it locally.
2. Create a virtual environment (`python -m venv venv`) and activate it.
3. Run `pip install -r requirements.txt`.
4. Copy `.env.example` to `.env` and configure your API Keys.
5. Create a new branch: `git checkout -b feature/your-feature-name`.

## 3. Pull Request Process
- Ensure any install or build dependencies are removed before the end of the layer when doing a build.
- Update the `README.md` and `README_ES.md` with details of changes to the interface, this includes new environment variables, exposed ports, useful file locations and container parameters.
- Provide a clear PR description outlining the mathematical logic if adding a new rule.

## 4. Proposing New PVU Cases

To propose new cases for the BeyondSight Reproducible Validation Package (PVU-BS):

1. Read the [Case Specification (EN)](docs/validation/pvu_case_spec_EN.md) or [(ES)](docs/validation/pvu_case_spec_ES.md) to understand the required file format.
2. Create a new directory under `datasets/pvu_cases/<your_case_id>/` with the four required files:
   - `meta.json` — case metadata (set `"is_synthetic": false` for real data).
   - `timeseries.csv` — time series with `t`, `date`, and `polarization` columns.
   - `interventions.json` — list of external events (can be `[]`).
   - `network.csv` — anonymised interaction network.
3. Complete and commit a [pre-registration template](docs/validation/preregistration_template_EN.md) **before** running the benchmark on your case.
4. Open a PR and include in the description:
   - The domain and data source (even if synthetic).
   - Whether the case is intended as a scientific case (counts toward N ≥ 10) or a CI sample.
   - Any licensing information for the underlying data.
5. The PVU CI workflow will automatically validate your case against the runner.

> **Note:** Scientific validation cases must satisfy the independence criteria defined in the protocol (§3 of `PVU_BeyondSight_EN.md`). Sample/synthetic cases are always welcome to improve CI coverage.

Happy simulating!
