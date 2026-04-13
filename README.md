---
title: BeyondSight
emoji: 🌊
colorFrom: blue
colorTo: indigo
sdk: streamlit
app_file: app.py
pinned: false
---

# BeyondSight: Strategy Engineering for Social Dynamics

[![License: PPL 3.0](https://img.shields.io/badge/License-PROSPERITY_PUBLIC_V3.0-blue.svg)](https://prosperitylicense.com)
[![tests](https://github.com/Adlgr87/BeyondSight/actions/workflows/pytest.yml/badge.svg)](https://github.com/Adlgr87/BeyondSight/actions/workflows/pytest.yml)
[![docs](https://github.com/Adlgr87/BeyondSight/actions/workflows/mkdocs.yml/badge.svg)](https://github.com/Adlgr87/BeyondSight/actions/workflows/mkdocs.yml)

![BeyondSight Demo](docs/beyondsight_mockup.png)

**BeyondSight** is a technical platform for **Inverse Social Simulation**.  
Instead of only forecasting outcomes, it computes the intervention path needed to reach a target social state.

In practical terms: you define a goal (for example, lower polarization, increase consensus, or trigger controlled adoption), and BeyondSight searches for the most coherent intervention strategy using simulation + AI reasoning.

It combines:
- **Mathematical social-dynamics models** (DeGroot, Hegselmann-Krause, Axelrod, threshold cascades).
- **Graph analytics** (centrality and bridge-node detection).
- **LLM-guided strategy search** to iteratively improve decisions.

The result is not just a chart, but an **actionable strategy itinerary** grounded in formal dynamics.

---

## ⚡ The Social Architect (Core Capability)

The core capability of BeyondSight is the **Social Architect**.  
Instead of manually tweaking parameters to see what happens, you define the objective:

> *"Achieve moderate consensus and eliminate polarization within 20 iterations, starting from a highly fragmented network."*

The Social Architect uses an **LLM-in-the-loop** architecture to:
1. **Analyze** network topology, group structure, and initial opinion states.
2. **Simulate** candidate intervention paths across multiple sociological regimes.
3. **Optimize** a `StrategyMatrix` (timed interventions + parameter schedules).
4. **Return** a clear intervention plan interpretable by analysts, researchers, and decision teams.

---

## 🧭 How BeyondSight Works (in 4 steps)

1. **Define target state**  
   Example: “Reach moderate consensus in ≤20 iterations without extreme polarization.”

2. **Run inverse search**  
   The Social Architect explores intervention sequences and evaluates trajectory quality at each loop.

3. **Validate with hybrid simulation**  
   Numerical models + graph metrics verify if the path is stable, realistic, and sociologically coherent.

4. **Export strategy**  
   Output includes the recommended intervention itinerary and supporting rationale.

---

## 🔬 Hybrid Simulation Architecture

BeyondSight bridges the gap between classic research and modern AI:

-   **Numerical Core:** Implements state-of-the-art models including DeGroot (influence), Hegselmann-Krause (clustering), and Axelrod (homophily).
-   **LLM Regime Selector:** A "heuristic brain" that analyzes historical trajectories and dynamically selects the most sociologically coherent transition regime at each step.
-   **Graph Intelligence:** Integrated NetworkX metrics (Degree/Betweenness Centrality) to identify bridge nodes and informal leaders for targeted interventions.

---

## 📖 Theoretical Foundations

The system is built on decades of peer-reviewed research:

-   **Hegselmann-Krause (2002):** Bounded confidence for clustering and polarization.
-   **Competitive Contagion (Beutel et al., 2012):** Spread of dual rival narratives.
-   **Heterogeneous Threshold (Granovetter, 1978):** Normal distribution of thresholds to model cascades.
-   **Confirmation Bias:** Selective exposure mechanisms as transversal filters.

---

## 🚀 Getting Started (Beginner Friendly)

### 1) Fastest way (recommended)

#### Windows
Double-click `start.bat` from the project folder.

Or run:
```bash
start.bat
```

#### macOS / Linux
```bash
chmod +x start.sh
./start.sh
```

What these scripts do automatically:
1. Create a local virtual environment (`.venv`) if it does not exist.
2. Install/update dependencies from `requirements.txt`.
3. Create `.env` from `.env.example` if missing.
4. Launch Streamlit at `http://localhost:8501`.

---

### 2) Manual local setup (advanced users)

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

---

### 3) API keys (only if you use cloud LLM providers)

Create `.env` from `.env.example` and fill the provider you will use:

- `GROQ_API_KEY`
- `OPENAI_API_KEY`
- `OPENROUTER_API_KEY`
- `OLLAMA_HOST` (for local Ollama, default: `http://localhost:11434`)

If you choose `ollama` in the UI, cloud API keys are not required.

---

### 4) Deploy to Hugging Face Spaces (simple path)

1. Create a new **Streamlit Space**.
2. Connect this repository.
3. In Space Settings → **Variables and secrets**, add your API keys.
4. Launch.

`app.py` is already configured as the Streamlit entrypoint.

---

### Troubleshooting

- **`streamlit` command not found**  
  Run through `start.bat` / `start.sh`, or ensure your virtual environment is activated.

- **Provider asks for API key**  
  Add the key to `.env` and restart the app.

- **Port already in use**  
  Run:
  ```bash
  streamlit run app.py --server.port 8502
  ```

- **Corporate network/proxy issues installing packages**  
  Configure your pip proxy and retry:
  ```bash
  pip install -r requirements.txt
  ```

### Advanced: Strategy Analysis via Gemini-CLI
For direct interaction with Google's Gemini models from your terminal — useful for deep-diving into generated strategies or performing manual audits:
```bash
npm install -g @google/gemini-cli
gemini
```

---

## 🔐 Security and API Management

BeyondSight supports Groq, OpenAI, and OpenRouter. Configure your keys in a `.env` file or environment variables:
- `GROQ_API_KEY`
- `OPENAI_API_KEY`
- `OPENROUTER_API_KEY`

---

## 📜 License

BeyondSight is distributed under the **Prosperity Public License 3.0.0**.
- **Non-Commercial:** Free for individuals, researchers, and educational purposes.
- **Commercial:** 30-day trial for businesses, followed by a commercial license requirement.

Contact [Adlgr87](https://github.com/Adlgr87) for commercial licensing.

---
*Engineering the future of social systems through AI-driven interpretability.*
