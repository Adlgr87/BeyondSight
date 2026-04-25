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

The project is inspired by fundamental opinion dynamics models and cutting-edge research.

### Base Models (Opinion Dynamics)

- **DeGroot and Friedkin-Johnsen Models:** Base implementation for opinion evolution in social networks, considering neighbor influence and resistance to change (prejudices).
- **Hegselmann-Krause (2002) - Bounded Confidence:** Agents only interact with groups whose opinion is within a radius `ε`, fostering natural polarization and cluster formation.
- **Competitive Contagion (Beutel et al., 2012):** Models the spread of two rival narratives competing simultaneously in the system.
- **Heterogeneous Threshold (Granovetter, 1978):** Uses a normal distribution of thresholds in the population instead of a static one, enabling rapid social cascade phenomena.
- **Co-evolutionary Networks and Homophily (Axelrod, 1997):** Influence intensity varies by opinion similarity, generating endogenous echo chambers.
- **Replicator Equation — Evolutionary Game Theory (Taylor & Jonker, 1978):** Strategy frequencies evolve according to relative payoff via the replicator ODE integrated with RK45.
- **Confirmation Bias:** A cognitive transversal mechanism that systematically attenuates the weight of information contrary to the agent's current belief.
- **Langevin Energy Dynamics:** Physics-inspired stochastic differential equations where agents move through a configurable social energy landscape of attractors and repellers — BeyondSight's newest simulation core.

### Extended Models

Three additional simulation rules (rules 10–12 in `extended_models.py`) expand the mathematical vocabulary of the Social Architect and the traditional simulator:

- **Nash Equilibrium — Game Theory (Nash, 1950):** Rule 10. Models stable mixed-strategy equilibria between social groups. At each step, a 2×2 coordination payoff matrix is built from the current opinion alignment with each group, and the Nash equilibrium mixed strategy determines group membership weights. Computed via `nashpy` (support enumeration) with an analytic 2×2 fallback.

- **Bayesian Opinion Network (Pearl, 1988):** Rule 11. A proper discrete Bayesian network (built with `pgmpy`) with nodes `Propaganda → Opinion ← Confianza, PresionSocial`. Evidence (propaganda level, institutional trust, social pressure) is discretized to 3 states; Variable Elimination returns the posterior opinion distribution. The posterior mean is mapped back to the continuous opinion space. Falls back to a Beta-Binomial conjugate model when `pgmpy` is unavailable.

- **SIR Epidemiological Contagion (Kermack & McKendrick, 1927):** Rule 12. Treats opinion adoption as an epidemic: Susceptible (can be influenced), Influenced (adopted), Resistant (immune to further change). Propaganda amplifies the effective contact rate `β`. The SIR ODE system is integrated with `scipy.integrate.solve_ivp` (RK45) at every simulation step.

### Hybrid Architecture

Unlike purely numerical simulations, BeyondSight uses an LLM (like Llama 3) to analyze historical trajectories and decide which mathematical transition regime is sociologically most coherent at each step. The heuristic fallback selector intelligently routes between all 13 rules (0–12) based on state conditions.

**Academic Connection:** BeyondSight's approach resonates with recent research like *"Opinion Consensus Formation Among Networked Large Language Models"* (January 2026), exploring how intelligent agents can reach consensus or polarization.

### Cross-Cutting Mechanisms

Three mechanisms are applied transversally on top of any simulation rule at every step:

- **Confirmation Bias (Sunstein 2009, Nickerson 1998):** Incoming information that contradicts the agent's current position is systematically attenuated proportionally to the configured bias level. At `sesgo_confirmacion = 1.0`, agents completely ignore counter-attitudinal propaganda.

- **Dynamic Homophily (Axelrod 1997, Flache et al. 2017):** Group influence weights update automatically each step based on opinion similarity — the more similar a group's opinion, the stronger its pull. This generates endogenous echo-chamber formation without explicit community assignment.

- **Strategic Game Theory Layer (Nash 1950, Axelrod 1984):** A payoff-based force (`utility_logic.py`) biases each agent toward cooperation or defection depending on neighbors' average position relative to the neutral point. A configurable 2×2 payoff matrix (Cooperation/Defection) and strategic weight ω control the intensity. Three pre-built game-theoretic presets (Prisoner's Dilemma, Stag Hunt, Coordination) plus a fully custom configuration are available in the UI.

### Early Warning Signals & Topological Analysis

BeyondSight monitors the simulation for proximity to tipping points using two complementary methods:

**Early Warning Signals (EWS) — Critical Slowing Down (Scheffer et al., 2009; Dakos et al., 2012):**  
Over a sliding window of the last 10 opinion values, the system continuously computes variance, lag-1 autocorrelation, and skewness. When any metric exceeds its threshold, a ⚠️ EWS warning is displayed in the UI — indicating that the system is approaching a bifurcation point and small perturbations may trigger large state changes.

**Topological Data Analysis — Persistent Homology (Carlsson, 2009; Perea & Harer, 2015):**  
When the optional `ripser` + `persim` packages are installed, BeyondSight performs Takens delay-embedding of the opinion time series and computes H1 persistence diagrams via Vietoris-Rips filtration. A significant Wasserstein distance between consecutive diagrams signals a topological regime change (`🔺 Topological change detected`) — a geometrically-grounded early warning that complements the statistical EWS indicators.

### Empirical Calibration Base

Modeling complex social phenomena requires anchoring simulations to measurable, real-world parameters.  
Academic research spanning psychology, political science, and network theory provides this empirical foundation.  
Jointly calibrated from more than 40 peer-reviewed sources, each parameter carries variance metadata for cultural adaptation.  
Opinion dynamics treated in isolation from data risks producing mathematically elegant but sociologically hollow results.  
Rooting the simulator in these calibration indices shifts BeyondSight from a theoretical toy to a research-grade instrument.  
Indices covering algorithmic drift, parasocial influence, confirmation bias, temporal decay, and game-theoretic payoffs are pre-loaded.  
Together, they form a living empirical base that researchers can extend by adding parameters or updating cultural variance estimates.  
Years of accumulated social science converge into a normalized bipolar spectrum, ready to inform every simulation step.  
Researchers and practitioners alike can query the master dictionary at runtime to inspect source citations and confidence levels.  
Evidence-grounded parameters prevent the simulator from drifting into pure speculation, keeping outputs interpretable and falsifiable.  
Providing this layer of empirical accountability is what distinguishes BeyondSight from a pure mathematical sandbox.  
Over upcoming releases, additional cultural blocks — Nordic, South Asian, Middle Eastern — will be populated with localized estimates.  
Remaining gaps are flagged with `pending_empirical_data` tags, making the boundaries of current knowledge explicit rather than hidden.  
Transparency about uncertainty is, ultimately, the most honest form of scientific modeling.

The master dictionary (`empirical_calibration.py`) consolidates 43 parameters spanning network dynamics, temporal decay, and game-theoretic payoffs, all normalized to the bipolar `[-1.0, 1.0]` spectrum used by every simulation rule. Six cultural blocks are tracked — Latino, Anglo-Saxon, East Asian, South Asian, Middle Eastern, and Nordic — and each parameter optionally carries block-specific variance values. Calibration indices are loaded at startup via `empirical_config.py`, which exposes the master dictionary and a `EMPIRICAL_BASE_LOADED` flag for downstream consumers. Parameters without empirical consensus are explicitly tagged `pending_empirical_data`.

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

BeyondSight introduces the **Social Architect**, an *LLM-in-the-loop* reverse engineering agent. Instead of predicting the future of a network, you define the sociological outcome you want (e.g., *"Achieve moderate consensus and eliminate polarization in 20 iterations"*), and the Social Architect works backwards to find the exact strategy that gets you there.

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

### LangChain Integration

When the **LangChain toggle** is enabled in the sidebar, both the Social Architect and the Programmatic Architect route their LLM calls through typed `LangChain` chains (`langchain_workflows.py`) instead of raw HTTP requests. Benefits:

- **Typed output parsing** — `JsonOutputParser` catches malformed JSON before it reaches the simulator.
- **Provider-agnostic** — supports `groq` (via `langchain-groq`), `openai`, `openrouter`, and `ollama` through the same chain interface.
- **Composable chains** — `strategy_chain`, `narrative_chain`, and `landscape_chain` can be extended with memory, tools, or agent executors in future iterations.

The fallback is always active: if LangChain is unavailable or the chain fails, the system reverts to direct HTTP calls.

## Installation

```bash
pip install -r requirements.txt
```

## Running the App

### Local Mode (Streamlit)
```bash
streamlit run app.py
```

The UI supports **English and Spanish** — use the Language toggle at the top of the sidebar to switch languages at any time.

### Running on Hugging Face Spaces
This repository is ready to be deployed as a **Hugging Face Space**. Simply connect this repo to a new Streamlit Space.

## Social Media Integration

BeyondSight can seed simulations with **real opinion data** fetched live from Twitter/X or Reddit. Configure credentials in the sidebar under **🌐 Datos de Redes Sociales**.

### Twitter / X

Requires a **Bearer Token** (Twitter Developer Portal → Project → App → Keys & Tokens).

| Credential | Where to get it |
|---|---|
| Bearer Token | [developer.twitter.com](https://developer.twitter.com) → Project → App → Keys & Tokens |

The connector queries the [Twitter v2 Recent Search API](https://developer.twitter.com/en/docs/twitter-api/tweets/search/introduction), applies keyword-based sentiment scoring, and returns the weighted mean opinion — ready to be used as the initial opinion state for any simulation.

### Reddit

Requires a **script-type application** registered at [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps).

| Credential | Description |
|---|---|
| Client ID | App's client ID (shown under the app name) |
| Client Secret | App's secret |
| User Agent | Any string, e.g. `BeyondSight/1.0` |

The connector uses `praw` to search a subreddit, scores each post's title + body for sentiment, weights by Reddit vote score, and returns a distribution of community opinions.

Both connectors work with **bipolar** `[-1, 1]` and **unipolar** `[0, 1]` ranges. You can set credentials via environment variables to avoid re-entering them:

```env
TWITTER_BEARER_TOKEN=xxx
REDDIT_CLIENT_ID=xxx
REDDIT_CLIENT_SECRET=xxx
```

## Performance Optimization

### Numba — JIT-accelerated Langevin Engine

The `SocialEnergyEngine` in `energy_engine.py` uses **Numba** to JIT-compile the inner Langevin step loop via `@njit`. On first call, the kernel is compiled once; all subsequent calls are native-speed (typically 5–20× faster than pure NumPy for large agent counts). Numba falls back gracefully with a no-op decorator when not installed.

### Dask — Parallel Multi-Simulation

The **⚡ Paralelizar con Dask** toggle in the UI activates `simular_multiples_dask()`, which wraps each of the N simulations in a `dask.delayed` task and executes them concurrently across all available CPU cores. For N=100 simulations, this typically provides a 3–8× speedup on multi-core machines. Falls back to sequential `simular_multiples()` when Dask is unavailable.

## Project Structure

```
BeyondSight/
├── tests/                        # Unit and integration tests
│   ├── test_energy_core.py       # Energy engine test suite (42 tests)
│   ├── test_game_theory.py       # Strategic Game Theory layer tests
│   ├── test_integration_llm.py   # LLM selector integration tests
│   ├── test_simulator.py         # Simulator core tests
│   ├── test_social_architect.py
│   └── test_visualizations.py
├── docs/                         # MkDocs documentation sources
├── .env.example                  # Environment variable template
├── .gitignore
├── app.py                        # Streamlit interface
├── cache_manager.py              # RAM + SQLite landscape cache
├── empirical_calibration.py      # Master empirical calibration dictionary (43 parameters)
├── empirical_config.py           # Calibration loader — EMPIRICAL_BASE_LOADED flag
├── energy_engine.py              # Langevin dynamics engine (Numba-accelerated)
├── energy_runner.py              # Langevin simulation orchestrator
├── energy_schemas.py             # Pydantic v2 schemas for EnergyConfig
├── extended_models.py            # Extended rules: Nash (10), Bayesian BN (11), SIR (12)
├── i18n.py                       # Internationalization helpers (English / Spanish)
├── langchain_workflows.py        # LangChain chains for Social & Programmatic Architects
├── programmatic_architect.py     # Programmatic Architect (archetypes + cache + LLM)
├── README.md                     # Documentation (English)
├── README_ES.md                  # Documentation (Spanish)
├── requirements.txt              # Dependencies
├── schemas.py                    # Pydantic schemas for StrategyMatrix and Game Theory
├── simulator.py                  # Simulator core: 13 rules, EWS, TDA, Dask parallel, LLM logic
├── social_architect.py           # Social Architect inverse-engineering agent
├── social_connectors.py          # Twitter/X and Reddit API connectors
├── utility_logic.py              # Game Theory strategic force calculator
└── visualizations.py             # Network visualization helpers
```

## Security

API keys can be managed via environment variables. Copy `.env.example` to `.env` and fill in your keys:

- `GROQ_API_KEY`
- `OPENAI_API_KEY`
- `OPENROUTER_API_KEY`
- `TWITTER_BEARER_TOKEN` *(optional — social media integration)*
- `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` *(optional — social media integration)*

In Hugging Face Spaces, you can set these as **Secrets**.

## License

This project is under the **Prosperity Public License 3.0.0**.

- **Communal/Personal/Educational Use:** Free and open.
- **Corporate Use:** Companies can test the software for 30 days. After that, a commercial license must be acquired.

For commercial inquiries, contact [Adlgr87](https://github.com/Adlgr87) on GitHub.

---
*Developed with a focus on AI interpretability and the study of complex social systems.*
