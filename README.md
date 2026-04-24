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

## 🧠 Social Architect — The Crown Jewel

The **Social Architect** is BeyondSight's flagship feature and its most powerful capability. Where traditional simulations ask *"what will happen?"*, the Social Architect answers: **"what must I do to make this happen?"**

### Concept: Sociological Reverse Engineering

You describe the **desired social outcome** in plain language — the final state you want a social network, community, or organization to reach. The Social Architect figures out the **exact sequence of interventions** (a mathematically grounded action plan) needed to drive the system from its current state to your goal.

Examples of what you can ask for:
- *"Eliminate polarization in 30 steps and achieve moderate consensus."*
- *"Gradually shift the majority opinion toward adoption of a new policy."*
- *"Dissolve an echo chamber and reconnect fragmented groups."*
- *"Reduce resistance to organizational change among informal leaders."*

The system responds with a **structured intervention schedule** (`StrategyMatrix`): a timeline of mathematical regimes, their parameters, and a human-readable sociological narrative explaining what each phase represents in the real world.

---

### Stochastic Dynamics: The Langevin Equations

BeyondSight models social opinion as a continuous stochastic process. At each discrete time step `t`, the opinion of the representative agent evolves according to a **discrete-time Langevin equation**:

```
x(t + Δt)  =  f(x(t), r(t))  ·  α  +  b(x(t))  ·  (1 − α)  +  G(x(t))  +  η(t)
```

Where:

| Term | Meaning |
|---|---|
| `f(x(t), r(t))` | Output of the active dynamical regime `r` (e.g., Hegselmann-Krause, threshold, memory, replicator…) |
| `α` (alpha blend) | Blending weight between LLM-selected model and base tendency (default 0.80) |
| `b(x(t))` | Base tendency: `0.92 · opinion + 0.08 · propaganda` — inertia and media pressure |
| `G(x(t))` | Group polarization effect — weighted influence of ideological clusters A and B |
| `η(t) ~ 𝒩(0, σ(t)²)` | **Stochastic Wiener increment** — Gaussian white noise representing social unpredictability |

The **adaptive noise coefficient** `σ(t)` is the Langevin diffusion term and captures the idea that **distrust amplifies social volatility**:

```
σ(t) = σ_base + σ_distrust · (1 − trust(t))
```

- `σ_base = 0.03` — irreducible background noise (spontaneous opinion drift)
- `σ_distrust = 0.08` — extra volatility injected when institutional trust is low
- `trust(t) ∈ [0, 1]` — dynamically updated each step

As trust erodes, the diffusion coefficient grows, producing wider fluctuations and making the system harder to steer — a mathematically grounded model of societal instability. In the multi-simulation probabilistic mode, each of the N runs receives an independent Wiener trajectory, yielding a **full probability distribution** of outcomes rather than a single deterministic path.

---

### The Iterative LLM–Simulation Loop

The Social Architect operates through a closed feedback loop that combines the reasoning power of an LLM with the rigor of mathematical simulation:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SOCIAL ARCHITECT LOOP                        │
│                                                                 │
│  1. USER INPUT                                                  │
│     Desired sociological outcome (free text) +                  │
│     Initial network state                                       │
│              │                                                  │
│              ▼                                                  │
│  2. LLM PROPOSAL                                                │
│     The LLM (GPT-4o, Llama 3, Mistral…) reads the goal and     │
│     proposes a StrategyMatrix: a JSON schedule of              │
│     interventions (model_name, parameters, time windows)        │
│              │                                                  │
│              ▼                                                  │
│  3. NUMERICAL SIMULATION                                        │
│     run_with_schedule() executes each intervention phase        │
│     through the Langevin engine, step by step                   │
│              │                                                  │
│              ▼                                                  │
│  4. EVALUATION                                                  │
│     Score 0–100 computed from polarization, opinion delta,      │
│     variance. Qualitative feedback generated.                   │
│              │                                                  │
│         Score ≥ 90? ──YES──► 5. NARRATIVE (success)            │
│              │                                                  │
│             NO                                                  │
│              │                                                  │
│  6. REFINEMENT                                                  │
│     Feedback injected into LLM context. LLM proposes a         │
│     corrected strategy. Loop repeats (up to max_attempts).      │
│              │                                                  │
│         Best attempt ──────► 5. NARRATIVE (best effort)         │
└─────────────────────────────────────────────────────────────────┘
```

**Step-by-step breakdown:**

1. **User Input:** You describe the target state in natural language and optionally set the initial network conditions (opinion, trust, propaganda, group membership).

2. **LLM Proposal:** An LLM (local via Ollama or cloud via Groq / OpenAI / OpenRouter) receives a system prompt that encodes its role as a sociological strategist and a user prompt containing the current network state, the goal, and any prior failed attempts. It outputs a structured `StrategyMatrix` JSON: a sequence of intervention phases, each specifying which mathematical regime to activate (`hk`, `umbral`, `memoria`, `contagio_competitivo`, etc.), its parameters, and a time window.

3. **Numerical Simulation:** `run_with_schedule()` steps through the timeline. In each phase, the specified dynamical regime is locked in and applied at every time step through the Langevin engine described above. The stochastic noise `η(t)` is re-sampled at every step, ensuring realistic randomness.

4. **Evaluation:** `evaluar_resultado()` computes a score (0–100) based on how close the final state is to the stated objective. It analyses mean polarization, total opinion drift (`delta`), and variance. Depending on the objective keywords (`"consenso"`, `"polariza"`, `"despolarizar"`, etc.), different success criteria apply.

5. **Refinement:** If the score is below 90, the feedback (what went wrong, which metrics were off) is appended to the LLM context and a new iteration begins. The LLM can see all prior failures and is expected to correct its strategy accordingly.

6. **Narrative:** Once a satisfactory strategy is found (or exhausted), `generar_narrativa_final()` asks the LLM to translate the dry mathematical schedule into a **rich sociological or organizational narrative** — explaining in human terms what each intervention phase represents in the real world.

---

### Two Operational Modes

| Mode | Use Case | Vocabulary & Framing |
|---|---|---|
| **Macro** | Public opinion, electoral campaigns, social media polarization, mass movements | Media campaigns, hashtags, echo chambers, political discourse, referendums |
| **Corporate** | Organizational change, HR, internal culture, team alignment | 1:1 meetings, OKRs, informal leaders, resistance to change, 30-60-90 day plans |

In **Corporate mode**, the Social Architect also receives network graph metrics (betweenness centrality, degree centrality) and can target specific high-influence nodes (informal leaders) as the primary recipients of early interventions, maximizing cascade effects within the organization.

---

### Output: The StrategyMatrix

The result is a validated `StrategyMatrix` object containing:
- A **sequence of intervention phases**, each with: start/end time, mathematical regime, parameters, and sociological rationale.
- A **score** reflecting how precisely the simulation matched the stated goal.
- A **final narrative** — a consultant-quality report explaining the full strategy in plain language.

The Social Architect is, in essence, an **AI sociological engineer**: it searches the combinatorial space of mathematical intervention sequences, validates each candidate through the Langevin simulation engine, and refines its proposals through LLM self-critique until it finds the recipe that mathematically achieves your desired social outcome.

---

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
