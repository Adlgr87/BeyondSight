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

Happy simulating!
