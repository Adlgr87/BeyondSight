---
title: BeyondSight
emoji: 🌊
colorFrom: blue
colorTo: indigo
sdk: streamlit
app_file: app.py
pinned: false
---

# BeyondSight

[![License: PPL 3.0](https://img.shields.io/badge/License-PROSPERITY_PUBLIC_V3.0-blue.svg)](https://prosperitylicense.com)
[![tests](https://github.com/Adlgr87/BeyondSight/actions/workflows/pytest.yml/badge.svg)](https://github.com/Adlgr87/BeyondSight/actions/workflows/pytest.yml)
[![docs](https://github.com/Adlgr87/BeyondSight/actions/workflows/mkdocs.yml/badge.svg)](https://github.com/Adlgr87/BeyondSight/actions/workflows/mkdocs.yml)

![BeyondSight Demo](docs/beyondsight_mockup.png)

Hybrid social dynamics simulator — Numerical core + LLM as regime selector.

BeyondSight bridges the gap between classic mathematical models of opinion formation and the contextual flexibility of Large Language Models (LLMs).

## Theoretical Foundations and Research

The project is inspired by fundamental opinion dynamics models and cutting-edge research:

- **DeGroot and Friedkin-Johnsen Models:** Base implementation for opinion evolution in social networks, considering neighbor influence and resistance to change (prejudices).
- **Hegselmann-Krause (2002) - Bounded Confidence:** Agents only interact with groups whose opinion is within a radius `ε`, fostering natural polarization and cluster formation.
- **Competitive Contagion (Beutel et al., 2012):** Models the spread of two rival narratives competing simultaneously in the system.
- **Heterogeneous Threshold (Granovetter, 1978):** Uses a normal distribution of thresholds in the population instead of a static one, enabling rapid social cascade phenomena.
- **Co-evolutionary Networks and Homophily (Axelrod, 1997):** Influence intensity varies by opinion similarity, generating endogenous echo chambers.
- **Confirmation Bias:** A cognitive transversal mechanism that systematically attenuates the weight of information contrary to the agent's current belief.
- **Academic Connection:** BeyondSight's approach resonates with recent research like *"Opinion Consensus Formation Among Networked Large Language Models"* (January 2026), exploring how intelligent agents can reach consensus or polarization.
- **Hybrid Architecture:** Unlike purely numerical simulations, BeyondSight uses an LLM (like Llama 3) to analyze historical trajectories and decide which mathematical transition regime is sociologically most coherent at each step.

## Social Architect (Reverse Engineering)

BeyondSight Enterprise introduces the **Social Architect**, an *LLM-in-the-loop* reverse engineering feature. Instead of predicting the future of a network, you provide the desired sociological outcome (e.g., "Achieve a moderate consensus and eliminate polarization in 20 iterations"). The heuristic LLM agent will iteratively run mathematical simulations, critique the timeline, and dynamically optimize the intervention variables until it discovers the exact interaction strategy (`StrategyMatrix`) required to mathematically achieve your exact goal.

## Installation

```bash
pip install -r requirements.txt
```

## Running the App

### Local Mode (Streamlit)
```bash
streamlit run app.py
```

### Running on Hugging Face Spaces
This repository is ready to be deployed as a **Hugging Face Space**. Simply connect this repo to a new Streamlit Space.

## Project Structure

```
BeyondSight/
├── archive/           # Historical versions and logs (git ignored)
├── tests/             # Unit and integration tests
├── .gitignore         # Ignored files configuration
├── app.py             # Streamlit interface
├── README.md          # Documentation (English)
├── README_ES.md       # Documentation (Spanish)
├── requirements.txt   # Dependencies
└── simulator.py       # Simulator core and LLM logic
```

## Security

API keys can be managed via environment variables. Copy `.env.example` to `.env` and fill in your keys:

- `GROQ_API_KEY`
- `OPENAI_API_KEY`
- `OPENROUTER_API_KEY`

In Hugging Face Spaces, you can set these as **Secrets**.

## License

This project is under the **Prosperity Public License 3.0.0**.

- **Communal/Personal/Educational Use:** Free and open.
- **Corporate Use:** Companies can test the software for 30 days. After that, a commercial license must be acquired.

For commercial inquiries, contact [Adlgr87](https://github.com/Adlgr87) on GitHub.

---
*Developed with a focus on AI interpretability and the study of complex social systems.*
