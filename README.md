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

At the heart of BeyondSight lies the **Social Architect** — a reverse-engineering LLM agent that discovers the precise sequence of mathematical interventions needed to steer any social network toward a desired outcome. Instead of predicting where a network *will* go, the Social Architect computes exactly *how to get* where you want it to go.

## Theoretical Foundations and Research

The project is inspired by fundamental opinion dynamics models and cutting-edge research:

- **DeGroot and Friedkin-Johnsen Models:** Base implementation for opinion evolution in social networks, considering neighbor influence and resistance to change (prejudices).
- **Hegselmann-Krause (2002) - Bounded Confidence:** Agents only interact with groups whose opinion is within a radius `ε`, fostering natural polarization and cluster formation.
- **Competitive Contagion (Beutel et al., 2012):** Models the spread of two rival narratives competing simultaneously in the system.
- **Heterogeneous Threshold (Granovetter, 1978):** Uses a normal distribution of thresholds in the population instead of a static one, enabling rapid social cascade phenomena.
- **Co-evolutionary Networks and Homophily (Axelrod, 1997):** Influence intensity varies by opinion similarity, generating endogenous echo chambers.
- **Confirmation Bias:** A cognitive transversal mechanism that systematically attenuates the weight of information contrary to the agent's current belief.
- **Langevin Energy Dynamics:** Physics-inspired stochastic differential equations where agents move through a configurable social energy landscape of attractors and repellers — BeyondSight's newest simulation core.
- **Academic Connection:** BeyondSight's approach resonates with recent research like *"Opinion Consensus Formation Among Networked Large Language Models"* (January 2026), exploring how intelligent agents can reach consensus or polarization.
- **Hybrid Architecture:** Unlike purely numerical simulations, BeyondSight uses an LLM (like Llama 3) to analyze historical trajectories and decide which mathematical transition regime is sociologically most coherent at each step.

## Energy Landscape Engine

BeyondSight's **Energy Landscape Engine** models social dynamics as a physical system where every agent's opinion evolves according to a Langevin stochastic differential equation:

```
x_i(t+η) = x_i(t) − η·∇U(x_i) + η·λ·(x̄_neighbors − x_i) + √(2η·T)·ε
```

| Term | Meaning |
|---|---|
| `∇U(x)` | Gradient of the social energy landscape (attractors/repellers) |
| `λ` (`lambda_social`) | Balance: 0 = pure landscape, 1 = pure social network influence |
| `T` (`temperature`) | Noise / free will — higher = more chaotic individual behavior |
| `ε ~ N(0,1)` | Stochastic term (Euler-Maruyama integration) |

**Attractors** model forces of social cohesion (consensus points, factional identities, official positions). **Repellers** model forces of social division (moderation aversion, anti-consensus dynamics). All parameters are validated via Pydantic v2 `EnergyConfig` schemas before any simulation runs.

### Pre-built Social Archetypes

The **Programmatic Architect** (`programmatic_architect.py`) ships with 8 validated archetypes covering the most common sociological scenarios:

| Archetype key | Description |
|---|---|
| `polarizacion_extrema` | Two irreconcilable camps. Center is no-man's land. |
| `polarizacion_moderada` | Two groups with possible dialogue at the center. |
| `consenso_moderado` | Society gravitates toward agreements. |
| `consenso_forzado` | Strong institutional pressure toward a single position. |
| `fragmentacion_3_grupos` | Three coexisting factions that don't merge. |
| `fragmentacion_4_grupos` | Four tribal communities with high segmentation. |
| `caos_social` | No clear structure. Each agent acts on its own impulse. |
| `radicalizacion_progresiva` | Agents start at center and are pulled toward extremes. |

**Resolution pipeline** — for any free-text goal, the engine tries in order:
1. **Exact archetype match** (instant, no API call)
2. **RAM cache** (sub-millisecond, same process)
3. **SQLite cache** (`LandscapeCache`) — persists across Streamlit sessions and container restarts
4. **LLM one-shot generation** (Groq / OpenAI / OpenRouter / Ollama) with Pydantic validation
5. **Fallback** to `caos_social` if LLM fails or returns invalid config

## Social Architect (Reverse Engineering)

BeyondSight Enterprise introduces the **Social Architect**, an *LLM-in-the-loop* reverse engineering agent. Instead of predicting the future of a network, you define the sociological outcome you want (e.g., *"Achieve moderate consensus and eliminate polarization in 20 iterations"*), and the Social Architect works backwards to find the exact strategy that gets you there.

### How It Works

1. **Goal definition:** You describe the desired end state in plain language — consensus, polarization, viral spread, crisis containment, cultural alignment, etc.
2. **Iterative simulation loop:** The LLM agent proposes a `StrategyMatrix` — a time-phased schedule of mathematical intervention regimes (HK, contagion, homophily, thresholds…). The simulator runs the schedule and scores the outcome.
3. **Self-critique and refinement:** If the score falls below the target, the agent receives structured feedback (polarization level, delta, variance) and proposes an improved strategy. Up to `N` refinement rounds are executed automatically.
4. **Narrative generation:** Once the optimal strategy is found, a second LLM call translates the mathematical parameters into a human-readable sociological or executive report — campaigns, policy levers, organizational actions — tailored to the operational mode.

### Operational Modes

| Mode | Domain | Vocabulary |
|---|---|---|
| **Macro** | Politics, public social networks, mass polarization | Media campaigns, viral hashtags, echo chambers, electoral polarization, influential nodes |
| **Corporate** | HR, organizational change, internal leadership | 1-on-1 sessions, interdepartmental meetings, top-down communication, 30-60-90 day action plans, OKR alignment |

In **Corporate mode**, the Social Architect identifies informal leaders (high betweenness centrality) as priority intervention targets, generating org-specific action plans instead of media strategies.

### Key Output: `StrategyMatrix`

The Social Architect returns a validated `StrategyMatrix` — a structured intervention schedule listing, for each time window: the mathematical regime, its tuning parameters, the targeted nodes (optional), and a plain-language rationale for that phase. This schedule can be exported, replayed in the simulator, or used as a blueprint for a real-world campaign.

> **Example goal →** *"Stabilize employee approval despite an ongoing reorganization."*
> **Output →** A 3-phase plan: first homophily-based cohesion among team leads, then a memory-stabilizing regime, finally a targeted top-down communication burst — with a full HR narrative explaining each phase in consulting language.

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
├── tests/                     # Unit and integration tests
│   ├── test_energy_core.py    # Energy engine test suite (42 tests)
│   ├── test_simulator.py      # Simulator core tests
│   ├── test_social_architect.py
│   └── test_visualizations.py
├── docs/                      # MkDocs documentation sources
├── .gitignore
├── app.py                     # Streamlit interface
├── cache_manager.py           # RAM + SQLite landscape cache
├── energy_engine.py           # Langevin dynamics engine (SocialEnergyEngine)
├── energy_runner.py           # Langevin simulation orchestrator
├── energy_schemas.py          # Pydantic v2 schemas for EnergyConfig
├── i18n.py                    # Internationalization helpers
├── programmatic_architect.py  # Programmatic Architect (archetypes + cache + LLM)
├── README.md                  # Documentation (English)
├── README_ES.md               # Documentation (Spanish)
├── requirements.txt           # Dependencies
├── schemas.py                 # Pydantic schemas for StrategyMatrix
├── simulator.py               # Simulator core and LLM logic
├── social_architect.py        # Social Architect inverse-engineering agent
└── visualizations.py          # Network visualization helpers
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
