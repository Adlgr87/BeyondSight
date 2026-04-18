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
- **Replicator Equation — EGT (Taylor & Jonker, 1978):** Two-strategy evolutionary game theory model. Population frequencies evolve according to relative payoff, using a configurable 2×2 payoff matrix integrated via RK45.
- **Confirmation Bias (Sunstein, 2009; Nickerson, 1998):** A transversal cognitive mechanism that systematically attenuates the weight of information contrary to the agent's current belief.
- **Early Warning Signals — EWS / Critical Slowing Down (Scheffer et al., 2009; Dakos et al., 2012):** Variance, lag-1 autocorrelation, and skewness are computed over a sliding opinion window to detect proximity to bifurcation tipping points.
- **Topological Data Analysis — TDA / Persistent Homology (Carlsson, 2009; Perea & Harer, 2015):** Optional advanced detection of topological changes in the opinion time series via Takens delay-embedding and Wasserstein distance between persistence diagrams. Activated when `ripser` and `persim` are installed.
- **Academic Connection:** BeyondSight's approach resonates with recent research like *"Opinion Consensus Formation Among Networked Large Language Models"* (January 2026), exploring how intelligent agents can reach consensus or polarization.
- **Hybrid Architecture:** Unlike purely numerical simulations, BeyondSight uses an LLM (like Llama 3) to analyze historical trajectories and decide which mathematical transition regime is sociologically most coherent at each step.

## Transition Rules

| ID | Name | Basis | When it dominates |
|---|---|---|---|
| 0 | Linear | Friedkin-Johnsen | Moderate conditions |
| 1 | Threshold | Granovetter (simple) | Propaganda crosses critical point |
| 2 | Memory | DeGroot with lag | Stable system, inertia |
| 3 | Backlash | Persuasion literature | Established rejection + propaganda |
| 4 | Polarization | Echo chamber | Trend already started |
| 5 | **HK** | Hegselmann-Krause (2002) | Groups very distant from each other |
| 6 | **Competitive Contagion** | Beutel et al. (2012) | Two active narratives |
| 7 | **Heterogeneous Threshold** | Granovetter (1978) | Social cascades |
| 8 | **Homophily** | Axelrod (1997) | Groups converge by similarity |
| 9 | **Replicator (EGT)** | Taylor & Jonker (1978) | Evolutionary pressure between group strategies |

**Cross-cutting Mechanisms:**
- **Confirmation Bias** — opposing propaganda arrives attenuated based on current position.
- **Dynamic Homophily** — group influence weights update every step based on opinion similarity.
- **Bipolar Range `[-1, 1]`** — active rejection has a direct and symmetrical expression with support.
- **Competing Narrative B** — enables competitive contagion between two simultaneous narratives.

## Opinion Ranges

| Situation | Range | Why |
|---|---|---|
| Vaccine, public policy, new product | **[-1, 1] bipolar** | Active rejection ≠ indifference |
| Elections, referendum | **[-1, 1] bipolar** | Voting against ≠ abstention |
| Technology adoption probability | **[0, 1] probabilistic** | Natural adoption rate |
| Information diffusion / contagion | **[0, 1] probabilistic** | SIR models in this range |

## Social Architect (Reverse Engineering)

BeyondSight Enterprise introduces the **Social Architect**, an *LLM-in-the-loop* reverse engineering feature. Instead of predicting the future of a network, you provide the desired sociological outcome (e.g., "Achieve a moderate consensus and eliminate polarization in 20 iterations"). The heuristic LLM agent will iteratively run mathematical simulations, critique the timeline, and dynamically optimize the intervention variables until it discovers the exact interaction strategy (`StrategyMatrix`) required to mathematically achieve your exact goal.

The Social Architect supports two operating modes:

- **🌐 Macro Mode** — Designed for political campaigns, public opinion, and massive social networks. Interventions are framed as media campaigns, political discourse, viral hashtags, echo chambers, and electoral polarization.
- **🏢 Corporate Mode** — Designed for HR, organizational change management, and internal corporate communication. Accepts a CSV of the organizational network (`source`, `target`) to calculate degree centrality and betweenness centrality via NetworkX, identifying formal leaders (high degree) and informal leaders (high betweenness). Interventions are framed as 1:1 meetings, internal communications, workshops, and 30-60-90 day action plans aligned with OKRs.

The agent uses **Pydantic schema validation** (`StrategyMatrix` / `Intervention`) to guarantee that each generated intervention schedule is structurally correct before being executed by the simulator.

## LLM Providers

| Provider | Description | Requires Key |
|---|---|---|
| `heurístico` | No LLM — deterministic logic, no cost or API key | No |
| `ollama` | Local LLM with Ollama — private, no per-call cost | No |
| `groq` | Groq Cloud — very fast, generous free tier | Yes |
| `openai` | OpenAI API — GPT-4o, GPT-4o-mini, etc. | Yes |
| `openrouter` | OpenRouter — access to hundreds of models with a single key | Yes |

## Probabilistic Mode

Activate **Multiple Simulations** to run N Monte Carlo runs with small perturbations on the initial state. The results return the final opinion distribution, P10–P90 confidence band, and probability of a positive position — suitable for scenario analysis and risk assessment.

## Early Warning Signals (EWS)

BeyondSight continuously monitors the opinion time series over a sliding window and raises alerts when:
- **High variance** — the system is becoming unstable.
- **High lag-1 autocorrelation** — critical slowing down, proximity to a tipping point.
- **High skewness** — asymmetric fluctuations, precursor to a regime shift.

When TDA is available, a topological change detector using Persistent Homology can also signal structural regime transitions.

## Social Network Visualization

After each simulation, BeyondSight generates an interactive **Plotly** graph of a synthetic network topology consistent with the final macroscopic state of the simulator — opinion polarization, trust levels, and group homophily are reflected in node colors and connection density.

## Internationalization

The full UI is available in **English** and **Spanish** via the `i18n.py` module. Language can be switched at any time from the sidebar.

## Installation

```bash
pip install -r requirements.txt
```

> **Optional TDA support:** `pip install ripser persim` enables Persistent Homology-based topological change detection.

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
├── docs/              # MkDocs documentation sources
├── tests/             # Unit and integration tests
├── .gitignore         # Ignored files configuration
├── app.py             # Streamlit interface
├── i18n.py            # Internationalization (English / Spanish)
├── schemas.py         # Pydantic schemas for StrategyMatrix validation
├── simulator.py       # Simulator core, all rules, EWS, TDA and LLM logic
├── social_architect.py# Social Architect agent (inverse / reverse mode)
├── visualizations.py  # Plotly social network topology visualization
├── mkdocs.yml         # MkDocs configuration
├── README.md          # Documentation (English)
├── README_ES.md       # Documentation (Spanish)
└── requirements.txt   # Dependencies
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
