"""
BeyondSight — Interfaz Streamlit
Simulador híbrido con soporte completo de modelos extendidos
"""

import json
import os
from collections import Counter

import numpy as np
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from i18n import t
from social_architect import buscar_estrategia_inversa
from visualizations import generate_social_network_viz
from simulator import (
    BEYONDSIGHT_EMPIRICAL_MASTER,
    BEYONDSIGHT_RUNTIME_PARAMS,
    DEFAULT_CONFIG,
    DEFAULT_PAYOFF_MATRIX,
    DESCRIPCIONES_REGLAS,
    NOMBRES_REGLAS,
    PROVEEDORES,
    RANGOS_DISPONIBLES,
    apply_empirical_profile,
    get_graph_metrics,
    resumen_historial,
    simular,
    simular_multiples,
    simular_multiples_dask,
)

# EMPIRICAL INTEGRATION — importar indicadores de base empírica si disponibles
try:
    from empirical_config import BEYONDSIGHT_RUNTIME_PARAMS as _EMPIRICAL_RUNTIME
    _EMPIRICAL_VALIDATION_FLAGS = _EMPIRICAL_RUNTIME.get("validation_flags", [])
except ImportError:
    _EMPIRICAL_VALIDATION_FLAGS = []

# Load environment variables from .env
load_dotenv()

# ------------------------------------------------------------
# GAME THEORY PRESETS (module-level constant)
# Payoff values are in the [-1, 1] bipolar range.
# ------------------------------------------------------------
# Keys are positional indices matching the i18n preset_options list:
#   0 → Custom / Personalizado
#   1 → Prisoner's Dilemma / Dilema del Prisionero
#   2 → Stag Hunt / Caza del Ciervo
#   3 → Coordination / Coordinación
_STRATEGIC_PRESETS: list[dict] = [
    # 0 — Custom: neutral starting point
    {"cc": 1.0, "cd": -1.0, "dc":  1.0, "dd": -1.0},
    # 1 — Prisoner's Dilemma: defection tempts but mutual defection is costly
    {"cc": 1.0, "cd": -1.0, "dc":  1.0, "dd": -0.5},
    # 2 — Stag Hunt: mutual cooperation pays most; solo defection yields zero
    {"cc": 1.0, "cd": -1.0, "dc":  0.0, "dd":  0.0},
    # 3 — Coordination: matching strategies rewarded, mismatches punished
    {"cc": 1.0, "cd": -1.0, "dc": -1.0, "dd":  1.0},
]

# ------------------------------------------------------------
# PÁGINA
# ------------------------------------------------------------
st.set_page_config(
    page_title="BeyondSight",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------
# ANALYTICS & SESSION STATE
# ------------------------------------------------------------
import streamlit.components.v1 as components
components.html("""
<script>
  // Google Analytics / PostHog script placeholder
  console.log('BeyondSight Analytics loaded');
</script>
""", width=0, height=0)

if "lead_captured" not in st.session_state:
    st.session_state["lead_captured"] = False
if "estr_inversa" not in st.session_state:
    st.session_state["estr_inversa"] = None
if "objetivo_inverso" not in st.session_state:
    st.session_state["objetivo_inverso"] = ""
if "corporate_graph" not in st.session_state:
    # Almacena el grafo NetworkX si se sube un CSV corporativo
    st.session_state["corporate_graph"] = None

# ------------------------------------------------------------
# ESTILOS
# ------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');
html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #0a0e14; color: #c5cdd9;
}
.stApp { background-color: #0a0e14; }
.bs-header {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2.2rem; font-weight: 600;
    color: #5ccfe6; letter-spacing: -0.5px; line-height: 1.1;
}
.bs-subtitle {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem; color: #3d5166;
    letter-spacing: 2px; text-transform: uppercase;
    margin-top: 4px; margin-bottom: 2rem;
}
.metric-card {
    background: #0d1520; border: 1px solid #1a2535;
    border-left: 3px solid #5ccfe6; border-radius: 4px;
    padding: 14px 18px; margin-bottom: 10px;
}
.metric-label {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem;
    color: #3d5166; text-transform: uppercase; letter-spacing: 1.5px;
}
.metric-value {
    font-family: 'IBM Plex Mono', monospace; font-size: 1.6rem;
    font-weight: 600; color: #5ccfe6; line-height: 1.2;
}
.metric-delta-pos { color: #bae67e; font-size: 0.85rem; }
.metric-delta-neg { color: #ff8f40; font-size: 0.85rem; }
.metric-delta-neu { color: #3d5166; font-size: 0.85rem; }
.badge {
    display: inline-block; font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem; padding: 3px 10px; border-radius: 3px; margin: 2px;
}
.log-entry {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem;
    color: #4d6680; padding: 3px 0; border-bottom: 1px solid #111820;
}
.log-entry:hover { color: #8ba7c0; }
section[data-testid="stSidebar"] {
    background-color: #0d1520; border-right: 1px solid #1a2535;
}
.stButton > button {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem;
    background: #0d1520; color: #5ccfe6; border: 1px solid #5ccfe6;
    border-radius: 3px; padding: 10px 28px; letter-spacing: 1px;
    text-transform: uppercase; transition: all 0.15s ease; width: 100%;
}
.stButton > button:hover { background: #5ccfe6; color: #0a0e14; }
.streamlit-expanderHeader {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem;
    color: #3d5166 !important; text-transform: uppercase; letter-spacing: 1px;
}
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------
st.markdown('<div class="bs-header">BeyondSight</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="bs-subtitle">Simulador híbrido · Dinámica social · LLM + Núcleo numérico</div>',
    unsafe_allow_html=True,
)

# EMPIRICAL INTEGRATION — mostrar aviso si hay parámetros sin datos empíricos
if _EMPIRICAL_VALIDATION_FLAGS:
    n_pending = len(_EMPIRICAL_VALIDATION_FLAGS)
    st.warning(
        f"⚠️ **{n_pending} parámetro{'s' if n_pending != 1 else ''} sin datos empíricos** "
        f"— usando lógica del motor",
        icon="🔬",
    )

# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------
with st.sidebar:

    st.markdown("### BeyondSight Enterprise")
    st.markdown("Gratis para uso no comercial (Prosperity Public License 3.0). Para agencias, corporativos y consultoría privada, se requiere Licencia Comercial.")
    st.link_button("💼 Adquirir Licencia Comercial", "mailto:BeyondSight@ejemplo.com")
    st.link_button("🤝 Contratar Consultoría", "mailto:BeyondSight@ejemplo.com")
    st.markdown("---")

    # ── LANGUAGE ───────────────────────────────────────────
    lang = st.radio("Language / Idioma", ["en", "es"], index=0, horizontal=True)

    st.markdown("---")

    # ── OPINION SPACE ──────────────────────────────────────
    st.markdown(t("opinion_space", lang))
    nombre_rango = st.radio(t("opinion_range", lang), list(RANGOS_DISPONIBLES.keys()), index=0)
    rango   = RANGOS_DISPONIBLES[nombre_rango]
    r_min, r_max, neutro = rango["min"], rango["max"], rango["neutro"]
    es_bipolar = r_min < 0
    defaults   = rango["defaults"]

    color_rango = "#c3a6ff" if es_bipolar else "#5ccfe6"
    etiqueta    = t("bipolar_label", lang) if es_bipolar else t("probabilistic_label", lang)
    st.markdown(
        f'<div class="badge" style="background:#0d1520;color:{color_rango};border:1px solid {color_rango}">'
        f'{etiqueta}</div>',
        unsafe_allow_html=True,
    )
    st.caption(rango["descripcion"])

    st.markdown("---")

    # ── LLM PROVIDER ──────────────────────────────────────
    st.markdown(t("llm_provider", lang))
    proveedor = st.selectbox(t("provider", lang), list(PROVEEDORES.keys()), index=0)
    st.caption(f"ℹ️ {PROVEEDORES[proveedor]['descripcion']}")

    api_key, modelo, ollama_host = "", "", DEFAULT_CONFIG["ollama_host"]

    # Try to get API Key from environment or st.secrets
    env_keys = {
        "groq": os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY"),
        "openai": os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY"),
        "openrouter": os.getenv("OPENROUTER_API_KEY") or st.secrets.get("OPENROUTER_API_KEY")
    }

    if proveedor == "ollama":
        ollama_host = st.text_input(t("ollama_host", lang), value=os.getenv("OLLAMA_HOST") or "http://localhost:11434")
        modelo = st.selectbox(t("model", lang), PROVEEDORES[proveedor]["modelos_sugeridos"])
        mc = st.text_input(t("write_exact_id", lang), placeholder="ej. deepseek-r1:7b")
        if mc.strip():
            modelo = mc.strip()
    elif proveedor in ("groq", "openai", "openrouter"):
        links = {"groq": "https://console.groq.com/keys",
                 "openai": "https://platform.openai.com/api-keys",
                 "openrouter": "https://openrouter.ai/keys"}
        st.markdown(f"[{t('get_api_key', lang)}]({links[proveedor]})")
        
        default_key = env_keys.get(proveedor) or ""
        api_key = st.text_input(t("api_key", lang), value=default_key, type="password")
        
        modelo  = st.selectbox(t("model", lang), PROVEEDORES[proveedor]["modelos_sugeridos"])
        mc = st.text_input(t("write_exact_id", lang))
        if mc.strip():
            modelo = mc.strip()

    usar_langchain = st.toggle("⛓️ Usar LangChain", value=False,
        help="Usa LangChain en lugar de llamadas HTTP directas al LLM. Requiere langchain instalado.")

    st.markdown("---")

    # ── INITIAL STATE ──────────────────────────────────────
    st.markdown(t("initial_state", lang))

    opinion0   = st.slider(t("initial_opinion", lang), r_min, r_max, float(defaults["opinion_inicial"]), 0.01)
    propaganda = st.slider(t("propaganda", lang),      r_min, r_max, float(defaults["propaganda"]),      0.01)
    confianza  = st.slider(t("institutional_trust", lang),  0.0, 1.0, float(defaults["confianza"]), 0.01)

    st.markdown("---")
    st.markdown(t("social_groups", lang))

    op_grupo_a  = st.slider(t("opinion_group_a", lang),      r_min, r_max, float(defaults["opinion_grupo_a"]), 0.01)
    op_grupo_b  = st.slider(t("opinion_group_b", lang), r_min, r_max, float(defaults["opinion_grupo_b"]), 0.01)
    pertenencia = st.slider(t("group_identity", lang), 0.0, 1.0, 0.65, 0.01)

    st.markdown("---")
    st.markdown(t("advanced_mechanisms", lang))

    sesgo_conf = st.slider(
        t("confirmation_bias", lang),
        0.0, 1.0, 0.3, 0.05
    )

    activar_narrativa_b = st.toggle(
        t("activate_narrative_b", lang),
        value=False
    )
    narrativa_b = 0.0
    if activar_narrativa_b:
        narrativa_b = st.slider(
            t("narrativa_b_intensity", lang),
            r_min, r_max,
            -0.3 if es_bipolar else 0.3,
            0.01
        )

    hk_epsilon = st.slider(
        t("hk_epsilon", lang),
        0.1, 0.8, 0.3, 0.05
    )

    homofilia_tasa = st.slider(
        t("homophily_rate", lang),
        0.0, 0.2, 0.05, 0.01
    )

    st.markdown("---")
    st.markdown(t("egt_section", lang))

    activar_replicador = st.toggle(t("activate_replicator", lang), value=False)
    payoff_matrix_cfg: list = list(DEFAULT_PAYOFF_MATRIX)
    dt_cfg: float = 0.1
    if activar_replicador:
        payoff_raw = st.text_area(
            t("payoff_matrix", lang),
            value=json.dumps(DEFAULT_PAYOFF_MATRIX),
            height=80,
            help="Introduce una matriz 2×2 en formato JSON. Ejemplo: [[1,0],[0,1]]",
        )
        try:
            parsed = json.loads(payoff_raw)
            if (
                isinstance(parsed, list)
                and len(parsed) == 2
                and all(isinstance(row, list) and len(row) == 2 for row in parsed)
            ):
                payoff_matrix_cfg = parsed
            else:
                st.error("La matriz debe ser 2×2. Usando identidad como fallback.")
        except json.JSONDecodeError:
            st.error("JSON inválido para la matriz de pagos. Usando identidad como fallback.")
        dt_cfg = st.slider(
            t("dt_step", lang),
            min_value=0.01, max_value=1.0, value=0.1, step=0.01,
        )

    st.markdown("---")
    st.markdown(t("strategic_section", lang))
    st.caption(t("strategic_help", lang))

    activar_strategic = st.toggle(t("activate_strategic", lang), value=False)
    strategic_cfg_ui: dict = {"enabled": False}
    if activar_strategic:
        # Game preset selector
        preset_options = t("strategic_preset_options", lang)
        preset_key = st.selectbox(t("strategic_preset", lang), preset_options)

        # Resolve preset values from module-level constant via index
        preset_idx = preset_options.index(preset_key)
        preset_vals = _STRATEGIC_PRESETS[preset_idx]

        col_cc, col_cd = st.columns(2)
        col_dc, col_dd = st.columns(2)
        with col_cc:
            cc_val = st.slider(t("strategic_cc", lang), -1.0, 1.0, preset_vals["cc"], 0.1)
        with col_cd:
            cd_val = st.slider(t("strategic_cd", lang), -1.0, 1.0, preset_vals["cd"], 0.1)
        with col_dc:
            dc_val = st.slider(t("strategic_dc", lang), -1.0, 1.0, preset_vals["dc"], 0.1)
        with col_dd:
            dd_val = st.slider(t("strategic_dd", lang), -1.0, 1.0, preset_vals["dd"], 0.1)

        omega = st.slider(t("strategic_weight", lang), 0.0, 1.0, 0.3, 0.05)

        strategic_cfg_ui = {
            "enabled": True,
            "payoff_matrix": {"cc": cc_val, "cd": cd_val, "dc": dc_val, "dd": dd_val},
            "strategic_weight": omega,
        }

    st.markdown("---")
    st.markdown(t("simulation_settings", lang))

    pasos       = st.slider(t("time_steps", lang),   20, 300, 60, 5)
    cada_n      = st.slider(t("llm_every_n", lang),    1,  20,  5, 1)
    alpha       = st.slider(t("blend_alpha", lang), 0.0, 1.0, 0.80, 0.05)

    st.markdown("---")
    st.markdown(t("probabilistic_mode", lang))
    modo_prob = st.toggle(t("activate_multi_sim", lang), value=False)
    n_sims = 50
    usar_dask = False
    if modo_prob:
        n_sims = st.slider(t("num_simulations", lang), 10, 200, 50, 10)
        usar_dask = st.toggle("⚡ Paralelizar con Dask", value=False,
            help="Usa Dask para paralelizar las simulaciones. Acelera el cálculo en máquinas con múltiples núcleos.")

    st.markdown("---")
    st.markdown("### 🌐 Datos de Redes Sociales")
    activar_social = st.toggle("Importar datos reales de RRSS", value=False)
    social_opinions = None

    if activar_social:
        red_social = st.radio("Red social", ["Twitter/X", "Reddit"], horizontal=True)
        query_social = st.text_input("Búsqueda / tema", placeholder="ej. climate change, inteligencia artificial")

        if red_social == "Twitter/X":
            bearer_token = st.text_input("Bearer Token", type="password", key="tw_bearer")
            if st.button("🐦 Obtener tweets") and query_social and bearer_token:
                try:
                    from social_connectors import TwitterConnector
                    conn = TwitterConnector(bearer_token=bearer_token)
                    result = conn.fetch_opinions(query_social, max_results=100,
                                                 range_type="bipolar" if es_bipolar else "unipolar")
                    social_opinions = result
                    st.success(f"✅ {result['n_tweets']} tweets analizados | opinión media: {result['mean_opinion']:+.3f}")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:  # Reddit
            reddit_client_id = st.text_input("Client ID", type="password", key="reddit_cid")
            reddit_secret    = st.text_input("Client Secret", type="password", key="reddit_sec")
            subreddit_name   = st.text_input("Subreddit", placeholder="ej. politics, worldnews")
            if st.button("🤖 Obtener posts") and query_social and reddit_client_id and reddit_secret and subreddit_name:
                try:
                    from social_connectors import RedditConnector
                    conn = RedditConnector(client_id=reddit_client_id, client_secret=reddit_secret)
                    result = conn.fetch_opinions(subreddit_name, query_social, limit=100,
                                                  range_type="bipolar" if es_bipolar else "unipolar")
                    social_opinions = result
                    st.success(f"✅ {result['n_posts']} posts de r/{subreddit_name} | opinión media: {result['mean_opinion']:+.3f}")
                except Exception as e:
                    st.error(f"Error: {e}")

        if social_opinions and len(social_opinions.get("opinions", [])) > 0:
            social_mean = float(social_opinions["mean_opinion"])
            st.caption(f"📊 σ={social_opinions['std_opinion']:.3f} | Opinión media de RRSS: {social_mean:+.3f}")
            usar_opinion_social = st.toggle(
                f"Usar {social_mean:+.3f} como opinión inicial (reemplaza el slider)",
                value=True,
                key="usar_opinion_social_toggle",
            )
            if usar_opinion_social:
                opinion0 = social_mean

    st.markdown("---")
    st.markdown("#### 🧪 Perfil Empírico" if lang == "es" else "#### 🧪 Empirical Profile")
    activar_empirico = st.toggle(
        "Aplicar calibración empírica (v{})".format(BEYONDSIGHT_EMPIRICAL_MASTER["meta"]["version"])
        if lang == "es"
        else "Apply empirical calibration (v{})".format(BEYONDSIGHT_EMPIRICAL_MASTER["meta"]["version"]),
        value=False,
        help=(
            "Aplica los índices de calibración empírica consolidados (redes, temporales, "
            "teoría de juegos) normalizados al rango [-1, 1]."
            if lang == "es"
            else "Applies consolidated empirical calibration indices (network dynamics, "
            "temporal effects, game theory) normalised to [-1, 1]."
        ),
    )
    if activar_empirico:
        rp = BEYONDSIGHT_RUNTIME_PARAMS
        st.caption(
            f"λ social={rp['social_influence_lambda']} · "
            f"T caos={rp['temperature']} · "
            f"atractor={rp['attractor_depth']} · "
            f"payoff cc={rp['payoff_coordination']} · "
            f"payoff dd={rp['payoff_defection']}"
        )

    st.markdown("---")
    correr = st.button(t("run_simulation", lang))


# ------------------------------------------------------------
# LÓGICA PRINCIPAL
# ------------------------------------------------------------
tab1, tab2 = st.tabs(['📊 Simulación Tradicional', '🧠 Arquitecto Social (Modo Inverso)'])

with tab1:
    if correr:

        if PROVEEDORES[proveedor]["requiere_key"] and not api_key.strip():
            st.error(f"⚠️ **{proveedor}** requiere API key.")
            st.stop()

        config_run = {
            "rango":              nombre_rango,
            "proveedor":          proveedor,
            "modelo":             modelo,
            "api_key":            api_key,
            "ollama_host":        ollama_host,
            "alpha_blend":        alpha,
            "sesgo_confirmacion": sesgo_conf,
            "hk_epsilon":         hk_epsilon,
            "homofilia_tasa":     homofilia_tasa,
            "usar_langchain":     usar_langchain,
        }
        if activar_replicador:
            config_run["modelo_matematico"] = "Replicator"
            config_run["payoff_matrix"]     = payoff_matrix_cfg
            config_run["dt"]                = dt_cfg
        if activar_strategic:
            config_run["strategic"] = strategic_cfg_ui
        if activar_empirico:
            config_run = apply_empirical_profile(config_run)

        estado_inicial = {
            "opinion":          opinion0,
            "propaganda":       propaganda,
            "confianza":        confianza,
            "opinion_grupo_a":  op_grupo_a,
            "opinion_grupo_b":  op_grupo_b,
            "pertenencia_grupo": pertenencia,
        }
        if activar_narrativa_b:
            estado_inicial["narrativa_b"] = narrativa_b

        with st.spinner(t("simulating", lang)):
            historial = simular(
                estado_inicial, pasos=pasos, cada_n_pasos=cada_n,
                config=config_run, verbose=False,
            )
            resultado_prob = None
            if modo_prob:
                if usar_dask:
                    resultado_prob = simular_multiples_dask(
                        estado_inicial, pasos=pasos, cada_n_pasos=cada_n,
                        config=config_run, n_simulaciones=n_sims,
                    )
                else:
                    resultado_prob = simular_multiples(
                        estado_inicial, pasos=pasos, cada_n_pasos=cada_n,
                        config=config_run, n_simulaciones=n_sims,
                    )

        stats     = resumen_historial(historial, config_run)
        opiniones = [h["opinion"] for h in historial]
        delta     = stats["delta_total"]

        # ── BADGES de mecanismos activos ───────────────────────
        badges = []
        if sesgo_conf > 0.1:
            badges.append(f'<span class="badge" style="background:#1a2535;color:#ff8f40;border:1px solid #ff8f40">sesgo={sesgo_conf:.2f}</span>')
        if activar_narrativa_b:
            badges.append(f'<span class="badge" style="background:#1a2535;color:#c3a6ff;border:1px solid #c3a6ff">narrativa B={narrativa_b:+.2f}</span>')
        if hk_epsilon != 0.3:
            badges.append(f'<span class="badge" style="background:#1a2535;color:#bae67e;border:1px solid #bae67e">HK ε={hk_epsilon:.2f}</span>')
        if activar_social and social_opinions and len(social_opinions.get("opinions", [])) > 0:
            src = social_opinions.get("query", "RRSS")
            badges.append(f'<span class="badge" style="background:#1a2535;color:#5ccfe6;border:1px solid #5ccfe6">📡 RRSS: {src[:20]}</span>')
        badges.append(
            f'<span class="badge" style="background:#0d1520;color:{color_rango};border:1px solid {color_rango}">'
            f'rango {nombre_rango.split("—")[0].strip()} · neutro={neutro}</span>'
        )
        st.markdown(" ".join(badges), unsafe_allow_html=True)

        # ── EWS / TDA INDICATORS ───────────────────────────────
        ews_final = historial[-1].get("ews", {})
        ews_flags_final = ews_final.get("flags", {})
        if any(ews_flags_final.values()):
            st.warning(
                t("ews_warning", lang,
                  hv=ews_flags_final.get("high_variance", False),
                  ha=ews_flags_final.get("high_autocorr", False),
                  hs=ews_flags_final.get("high_skewness", False)),
            )

        tda_final = historial[-1].get("tda_change", False)
        if tda_final:
            st.error(t("tda_change", lang))

        # ── MÉTRICAS ───────────────────────────────────────────
        st.markdown(t("results", lang))
        c1, c2, c3, c4 = st.columns(4)

        delta_cls = "metric-delta-pos" if delta > 0 else ("metric-delta-neg" if delta < -0.01 else "metric-delta-neu")
        delta_sym = "▲" if delta > 0.01 else ("▼" if delta < -0.01 else "◆")

        with c1:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-label">{t('final_opinion', lang)}</div>
                <div class="metric-value">{stats['opinion_final']:+.3f}</div>
                <div class="{delta_cls}">{delta_sym} {delta:+.3f} {t('vs_start', lang)}</div>
            </div>""", unsafe_allow_html=True)

        with c2:
            pol     = stats["polarizacion_media"]
            amp     = r_max - r_min
            pol_cls = "metric-delta-neg" if pol > 0.3 * amp else "metric-delta-neu"
            st.markdown(f"""<div class="metric-card">
                <div class="metric-label">{t('avg_polarization', lang)}</div>
                <div class="metric-value">{pol:.3f}</div>
                <div class="{pol_cls}">{t('dist_to_neutral', lang)} ({neutro})</div>
            </div>""", unsafe_allow_html=True)

        with c3:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-label">{t('mean_std', lang)}</div>
                <div class="metric-value">{stats['media']:+.3f}</div>
                <div class="metric-delta-neu">σ = {stats['desviacion']:.3f}</div>
            </div>""", unsafe_allow_html=True)

        with c4:
            regla_dom     = stats.get("regla_dominante", "—")
            reglas_usadas = [h.get("_regla_nombre", "") for h in historial if "_regla_nombre" in h]
            n_dom         = Counter(reglas_usadas).get(regla_dom, 0)
            st.markdown(f"""<div class="metric-card">
                <div class="metric-label">{t('dominant_regime', lang)}</div>
                <div class="metric-value" style="font-size:1.0rem">{regla_dom}</div>
                <div class="metric-delta-neu">{n_dom}/{pasos} {t('time_steps', lang).lower()}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── GRÁFICO PRINCIPAL ──────────────────────────────────
        col_g, col_s = st.columns([3, 1])

        with col_g:
            df_data = {
                "Opinión":         opiniones,
                "Neutro":          [neutro]     * len(opiniones),
                "Narrativa A":     [propaganda] * len(opiniones),
                "Grupo afín":      [op_grupo_a] * len(opiniones),
                "Grupo contrario": [op_grupo_b] * len(opiniones),
            }
            if activar_narrativa_b:
                df_data["Narrativa B"] = [narrativa_b] * len(opiniones)

            st.markdown("**Trayectoria de opinión**")
            st.line_chart(
                pd.DataFrame(df_data),
                color=["#5ccfe6", "#3d5166", "#ff8f40", "#bae67e", "#f28779"]
                      + (["#c3a6ff"] if activar_narrativa_b else []),
            )
            
            st.markdown("### Topología de Red Social (Física)")
            fig_net = generate_social_network_viz(opiniones[-1], historial[-1]["confianza"], amalgama=not es_bipolar, is_bipolar=es_bipolar)
            st.plotly_chart(fig_net, use_container_width=True)
            
            share_url = "https://github.com/Adlgr87/BeyondSight"
            st.markdown(f"**¿Impresionante?** [Compartir en 𝕏](https://twitter.com/intent/tweet?text=Acabo%20de%20simular%20una%20dinámica%20social%20en%20BeyondSight%20AI!%20&url={share_url}) | [Compartir en LinkedIn](https://www.linkedin.com/sharing/share-offsite/?url={share_url})")

        with col_s:
            st.markdown("**Distribución de reglas**")
            conteo = Counter(reglas_usadas)
            df_r   = pd.DataFrame({
                "Regla": list(conteo.keys()),
                "Pasos": list(conteo.values()),
            }).sort_values("Pasos", ascending=False)
            st.dataframe(df_r, use_container_width=True, hide_index=True)

            # Evolución de pertenencia al grupo (si homofilia cambió algo)
            pertens = [h.get("pertenencia_grupo", pertenencia) for h in historial]
            if max(pertens) - min(pertens) > 0.01:
                st.markdown("**Evolución de identidad grupal**")
                st.line_chart(pd.DataFrame({"Identidad grupal": pertens}))

        # ── MODO PROBABILÍSTICO ────────────────────────────────
        if resultado_prob:
            rp = resultado_prob
            st.markdown("### Distribución probabilística")
            cc1, cc2, cc3 = st.columns(3)
            with cc1:
                st.markdown(f"""<div class="metric-card">
                    <div class="metric-label">Media final</div>
                    <div class="metric-value">{rp['media']:+.3f}</div>
                    <div class="metric-delta-neu">σ = {rp['std']:.3f}</div>
                </div>""", unsafe_allow_html=True)
            with cc2:
                prob  = rp["p_sobre_neutro"]
                pcls  = "metric-delta-pos" if prob > 0.6 else ("metric-delta-neg" if prob < 0.4 else "metric-delta-neu")
                st.markdown(f"""<div class="metric-card">
                    <div class="metric-label">P(opinión > {neutro})</div>
                    <div class="metric-value">{prob:.1%}</div>
                    <div class="{pcls}">probabilidad posición positiva</div>
                </div>""", unsafe_allow_html=True)
            with cc3:
                st.markdown(f"""<div class="metric-card">
                    <div class="metric-label">Rango P10–P90</div>
                    <div class="metric-value">{rp['percentiles']['p10']:+.2f} – {rp['percentiles']['p90']:+.2f}</div>
                    <div class="metric-delta-neu">banda de confianza 80%</div>
                </div>""", unsafe_allow_html=True)

            st.line_chart(pd.DataFrame({
                "Trayectoria": opiniones,
                "Optimista":   [rp["escenarios"]["optimista"]] * len(opiniones),
                "Mediano":     [rp["escenarios"]["mediano"]]   * len(opiniones),
                "Pesimista":   [rp["escenarios"]["pesimista"]] * len(opiniones),
                "Neutro":      [neutro]                        * len(opiniones),
            }), color=["#5ccfe6", "#bae67e", "#ff8f40", "#f28779", "#3d5166"])

        # ── LOG ────────────────────────────────────────────────
        with st.expander("🔍 Log de decisiones del selector"):
            cambios = [h for h in historial[1:] if h.get("_paso", 0) % cada_n == 0]
            for h in cambios:
                extras = ""
                if "_fraccion_adoptantes" in h:
                    extras += f" | adoptantes={h['_fraccion_adoptantes']:.2f}"
                if "_sim_grupo_a" in h:
                    extras += f" | sim_A={h['_sim_grupo_a']:.2f} sim_B={h.get('_sim_grupo_b',0):.2f}"
                if "_nash_sigma_a" in h:
                    extras += f" | Nash σ_A={h['_nash_sigma_a']:.2f}"
                if "_bayes_uncertainty" in h:
                    extras += f" | BN uncertainty={h['_bayes_uncertainty']:.4f}"
                if "_sir_I" in h:
                    extras += f" | SIR I={h['_sir_I']:.3f} R={h['_sir_R']:.3f}"
                st.markdown(
                    f'<div class="log-entry">t={h.get("_paso","?"):3} │ '
                    f'<b>{h.get("_regla_nombre","?")}</b> │ '
                    f'op={h.get("opinion",0):+.3f} │ {h.get("_razon","")}{extras}</div>',
                    unsafe_allow_html=True,
                )

        # ── EXPORTAR ───────────────────────────────────────────
        with st.expander("⬇️ Exportar"):
            df_exp  = pd.DataFrame(historial)
            cols    = ["opinion", "propaganda", "confianza", "pertenencia_grupo",
                       "_paso", "_regla_nombre", "_razon", "_rango",
                       "_fraccion_adoptantes", "_sim_grupo_a", "_sim_grupo_b"]
            cols_ok = [c for c in cols if c in df_exp.columns]
            st.dataframe(df_exp[cols_ok], use_container_width=True)
            ca, cb  = st.columns(2)
            with ca:
                st.download_button("⬇ CSV",
                    data=df_exp[cols_ok].to_csv(index=False),
                    file_name="beyondsight.csv", mime="text/csv")
            with cb:
                st.download_button("⬇ JSON",
                    data=json.dumps(historial, indent=2, default=str),
                    file_name="beyondsight.json", mime="application/json")

    # ------------------------------------------------------------
    # EMPTY STATE
    # ------------------------------------------------------------
    else:
        st.markdown(f"""
        <div style="border:1px dashed #1a2535;border-radius:4px;padding:48px;text-align:center;margin-top:2rem;">
            <div style="font-family:'IBM Plex Mono',monospace;color:#3d5166;font-size:0.8rem;letter-spacing:2px;">
                {t('empty_state', lang)}
            </div>
        </div>""", unsafe_allow_html=True)

        with st.expander(t("guide_expander", lang)):
            st.markdown(t("model_guide_content", lang))

        with st.expander(t("range_guide_expander", lang)):
            st.markdown(t("range_guide_content", lang))


with tab2:
    st.markdown("### Arquitecto Social: Ingeniería Inversa 🧠")
    st.markdown(
        "Describe el **clima social final** que deseas lograr en la red y nuestro Agente LLM "
        "iterará con los modelos matemáticos hasta encontrar la receta sociológica exacta."
    )

    # ── SELECTOR DE MODO ─────────────────────────────────────────
    modo_cols = st.columns([1, 1])
    with modo_cols[0]:
        modo_simulacion = st.radio(
            "**Modo de Simulación**",
            options=["macro", "corporativo"],
            format_func=lambda m: "🌐 Modo Macro (Redes Sociales/Políticas)" if m == "macro" else "🏢 Modo Corporativo (Organizaciones)",
            horizontal=True,
        )

    # ── CARGA DE CSV CORPORATIVO ──────────────────────────────────
    grafo_org = st.session_state.get("corporate_graph", None)
    metricas_red = ""

    if modo_simulacion == "corporativo":
        st.markdown("---")
        st.markdown("#### Red Organizacional")
        csv_col, metrics_col = st.columns([3, 2])
        with csv_col:
            csv_uploaded = st.file_uploader(
                "📂 Sube tu CSV de red (columnas: `source`, `target`)",
                type=["csv"],
                help="Cada fila representa una conexión entre dos personas/departamentos.",
            )
            if csv_uploaded is not None:
                try:
                    import networkx as nx
                    df_csv = pd.read_csv(csv_uploaded)
                    if "source" in df_csv.columns and "target" in df_csv.columns:
                        G = nx.from_pandas_edgelist(df_csv, source="source", target="target")
                        st.session_state["corporate_graph"] = G
                        grafo_org = G
                        st.success(f"✅ Red cargada: **{G.number_of_nodes()}** nodos, **{G.number_of_edges()}** conexiones.")
                    else:
                        st.error("El CSV necesita columnas 'source' y 'target'.")
                except Exception as e:
                    st.error(f"Error al cargar el CSV: {e}")

        with metrics_col:
            if grafo_org is not None:
                metricas_red = get_graph_metrics(grafo_org, modo="corporativo", top_n=5)
                st.markdown("**Métricas de la Red:**")
                st.code(metricas_red, language="text")
            else:
                st.info("Sin CSV cargado. Se usará una red organizacional genérica.")
                # Red sintética de demo para modo corporativo sin CSV
                import networkx as nx
                G_demo = nx.barabasi_albert_graph(20, 2, seed=42)
                G_demo = nx.relabel_nodes(G_demo, {i: f"Nodo_{chr(65+i%26)}{i//26 or ''}" for i in G_demo.nodes()})
                metricas_red = get_graph_metrics(G_demo, modo="corporativo", top_n=5)
                # Mostrar advertencia amigable
                st.caption(f"🔁 Red demo (20 nodos, Barabási-Albert):\n{metricas_red}")

    elif modo_simulacion == "macro":
        metricas_red = ""  # En modo macro no se usan métricas de grafo

    st.markdown("---")

    # ── OBJETIVO Y EJECUCIÓN ──────────────────────────────────────
    placeholder_objetivo = (
        "Ej: 'Quiero alinear al equipo de ventas con la nueva estrategia en 30 días, "
        "empezando por los líderes informales identificados.'"
        if modo_simulacion == "corporativo" else
        "Ej: 'Quiero despolarizar una red dividida en dos bandos radicales y lograr un consenso moderado.'"
    )
    objetivo = st.text_area("✏️ Describe tu objetivo:", placeholder=placeholder_objetivo, height=100)
    usar_langchain_arq = st.toggle("⛓️ Arquitecto con LangChain", value=False,
        help="Usa LangChain chains en lugar de HTTP directo")

    if st.button("⚡ Generar Estrategia Maestra"):
        if objetivo:
            if PROVEEDORES[proveedor]["requiere_key"] and not api_key.strip():
                st.error("⚠️ Se requiere API key para generar estrategias con el LLM.")
                st.stop()

            config_run = {
                "rango": nombre_rango,
                "proveedor": proveedor,
                "modelo": modelo,
                "api_key": api_key,
                "ollama_host": ollama_host,
                "alpha_blend": alpha,
                "sesgo_confirmacion": sesgo_conf,
                "hk_epsilon": hk_epsilon,
                "homofilia_tasa": homofilia_tasa,
                # Pasar tamaño del grafo para el cálculo de proporciones target_nodes
                "_n_nodos": grafo_org.number_of_nodes() if grafo_org else 20,
            }
            if activar_replicador:
                config_run["modelo_matematico"] = "Replicator"
                config_run["payoff_matrix"]     = payoff_matrix_cfg
                config_run["dt"]                = dt_cfg
            if activar_strategic:
                config_run["strategic"] = strategic_cfg_ui
            estado_inicial = {
                "opinion": opinion0,
                "propaganda": propaganda,
                "confianza": confianza,
                "opinion_grupo_a": op_grupo_a,
                "opinion_grupo_b": op_grupo_b,
                "pertenencia_grupo": pertenencia,
            }
            if activar_narrativa_b:
                estado_inicial["narrativa_b"] = narrativa_b

            # Badge de modo
            modo_badge_color = "#c3a6ff" if modo_simulacion == "corporativo" else "#5ccfe6"
            modo_label = "🏢 Corporativo" if modo_simulacion == "corporativo" else "🌐 Macro"
            st.markdown(
                f'<span class="badge" style="background:#1a2535;color:{modo_badge_color};'
                f'border:1px solid {modo_badge_color}">{modo_label}</span>',
                unsafe_allow_html=True,
            )

            with st.status(
                f"Arquitecto trabajando en modo **{modo_label}**... esto puede tomar un minuto.",
                expanded=True
            ) as status:
                st.write("Calculando simulaciones hipotéticas y escenarios de convergencia...")
                if metricas_red:
                    st.write(f"🔍 Métricas de red inyectadas en el prompt del LLM.")

                estrategia, narrativa, intentos, hist_inverso = buscar_estrategia_inversa(
                    estado_inicial=estado_inicial,
                    objetivo_usuario=objetivo,
                    max_intentos=3,
                    config=config_run,
                    modo_simulacion=modo_simulacion,
                    metricas_red=metricas_red,
                    use_langchain=usar_langchain_arq,
                )
                st.session_state["estr_inversa"] = {
                    "estrategia": estrategia,
                    "narrativa": narrativa,
                    "hist_inverso": hist_inverso,
                    "modo": modo_simulacion,
                }
                st.session_state["objetivo_inverso"] = objetivo
                status.update(
                    label=f"Estrategia encontrada en {intentos} iteraciones!",
                    state="complete",
                    expanded=False,
                )
                st.rerun()
        else:
            st.warning("Por favor, describe un objetivo.")

    if st.session_state["estr_inversa"]:
        data_inv = st.session_state["estr_inversa"]
        modo_inv = data_inv.get("modo", "macro")

        if not st.session_state["lead_captured"]:
            st.success("¡Estrategia calculada con éxito!")
            st.write("Para desbloquear el **Reporte Estratégico Completo** y la matriz de intervención, ingresa tu email corporativo.")
            with st.form("lead_form"):
                email = st.text_input("Email Corporativo:")
                submit = st.form_submit_button("🔓 Desbloquear Reporte")
                if submit and email:
                    with open("leads.csv", "a") as f:
                        f.write(email + "\n")
                    st.session_state["lead_captured"] = True
                    st.rerun()
        else:
            titulo_narrativa = (
                "📋 Reporte Ejecutivo de Cambio Organizacional"
                if modo_inv == "corporativo" else
                "🌐 Análisis de Clima Social"
            )
            st.subheader(titulo_narrativa)
            st.write(data_inv["narrativa"])

            if data_inv["hist_inverso"]:
                st.markdown("**Trayectoria de opinión (Estrategia Aplicada)** — *BeyondSight AI*")
                opiniones_inv = [h["opinion"] for h in data_inv["hist_inverso"]]
                df_data_inv = {"Opinión": opiniones_inv, "Neutro": [neutro] * len(opiniones_inv)}
                st.line_chart(pd.DataFrame(df_data_inv), color=["#5ccfe6", "#3d5166"])

                st.markdown("### Topología de Red Empírica")
                fig_net2 = generate_social_network_viz(
                    opiniones_inv[-1], 0.5,
                    amalgama=not es_bipolar, is_bipolar=es_bipolar
                )
                st.plotly_chart(fig_net2, use_container_width=True)

            # ── MATRIZ CON TARGET NODES RESALTADOS ───────────────
            st.subheader("Matriz de Intervención (Datos Técnicos)")
            estrategia_display = data_inv["estrategia"]
            # Resaltar fases con target_nodes en modo corporativo
            if modo_inv == "corporativo":
                fases_con_targets = [
                    f for f in estrategia_display.get("interventions", [])
                    if f.get("target_nodes") or (
                        isinstance(f.get("parameters", {}), dict)
                        and f["parameters"].get("target_nodes")
                    )
                ]
                if fases_con_targets:
                    st.markdown(
                        f"🎯 **{len(fases_con_targets)} fase(s) con intervención directa en nodos líderes.**"
                    )
            st.json(estrategia_display)

            report_text = (
                f"REPORTE EJECUTIVO - ARQUITECTO SOCIAL\n"
                f"Modo: {modo_inv.upper()}\n"
                f"Objetivo: {st.session_state['objetivo_inverso']}\n\n"
                f"{data_inv['narrativa']}\n\n"
                "MATRIZ:\n" + json.dumps(data_inv["estrategia"], indent=2) + "\n\n"
                + "-" * 50 + "\n"
                + "Generado con BeyondSight AI - Simulador de Redes Sociales.\n"
                + "Descubre más y obtén tu licencia en: https://github.com/Adlgr87/BeyondSight\n"
                + "-" * 50
            )
            st.download_button(
                "📥 Descargar Reporte Ejecutivo (TXT)",
                data=report_text,
                file_name=f"Reporte_BeyondSight_{modo_inv.capitalize()}.txt",
            )
