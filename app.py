"""
BeyondSight — Interfaz Streamlit
Simulador híbrido con soporte completo de modelos extendidos
"""

import json
from collections import Counter

import numpy as np
import pandas as pd
import streamlit as st

from simulator import (
    DEFAULT_CONFIG,
    DESCRIPCIONES_REGLAS,
    NOMBRES_REGLAS,
    PROVEEDORES,
    RANGOS_DISPONIBLES,
    resumen_historial,
    simular,
    simular_multiples,
)

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

# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------
with st.sidebar:

    # ── RANGO ──────────────────────────────────────────────
    st.markdown("#### 📐 Espacio de opinión")
    nombre_rango = st.radio("Rango de valores", list(RANGOS_DISPONIBLES.keys()), index=0)
    rango   = RANGOS_DISPONIBLES[nombre_rango]
    r_min, r_max, neutro = rango["min"], rango["max"], rango["neutro"]
    es_bipolar = r_min < 0
    defaults   = rango["defaults"]

    color_rango = "#c3a6ff" if es_bipolar else "#5ccfe6"
    etiqueta    = "[-1 rechazo] ← 0 → [+1 apoyo]" if es_bipolar else "[0] → [0.5 neutro] → [1]"
    st.markdown(
        f'<div class="badge" style="background:#0d1520;color:{color_rango};border:1px solid {color_rango}">'
        f'{etiqueta}</div>',
        unsafe_allow_html=True,
    )
    st.caption(rango["descripcion"])

    st.markdown("---")

    # ── PROVEEDOR LLM ──────────────────────────────────────
    st.markdown("#### 🤖 Proveedor LLM")
    proveedor = st.selectbox("Proveedor", list(PROVEEDORES.keys()), index=0)
    st.caption(f"ℹ️ {PROVEEDORES[proveedor]['descripcion']}")

    api_key, modelo, ollama_host = "", "", DEFAULT_CONFIG["ollama_host"]

    if proveedor == "ollama":
        ollama_host = st.text_input("Host Ollama", value="http://localhost:11434")
        modelo = st.selectbox("Modelo", PROVEEDORES[proveedor]["modelos_sugeridos"])
        mc = st.text_input("O escribe otro:", placeholder="ej. deepseek-r1:7b")
        if mc.strip():
            modelo = mc.strip()
    elif proveedor in ("groq", "openai", "openrouter"):
        links = {"groq": "https://console.groq.com/keys",
                 "openai": "https://platform.openai.com/api-keys",
                 "openrouter": "https://openrouter.ai/keys"}
        st.markdown(f"[Obtener API key →]({links[proveedor]})")
        api_key = st.text_input("API Key", type="password")
        modelo  = st.selectbox("Modelo", PROVEEDORES[proveedor]["modelos_sugeridos"])
        mc = st.text_input("O escribe el ID exacto:")
        if mc.strip():
            modelo = mc.strip()

    st.markdown("---")

    # ── ESTADO INICIAL ─────────────────────────────────────
    st.markdown("#### 🌍 Estado inicial")

    opinion0   = st.slider("Opinión inicial",          r_min, r_max, float(defaults["opinion_inicial"]), 0.01)
    propaganda = st.slider("Narrativa principal (A)",  r_min, r_max, float(defaults["propaganda"]),      0.01,
                            help="En modo bipolar: negativo = contra-narrativa activa.")
    confianza  = st.slider("Confianza institucional",  0.0, 1.0, float(defaults["confianza"]), 0.01)

    st.markdown("---")
    st.markdown("#### 👥 Grupos sociales")

    op_grupo_a  = st.slider("Opinión grupo afín",      r_min, r_max, float(defaults["opinion_grupo_a"]), 0.01)
    op_grupo_b  = st.slider("Opinión grupo contrario", r_min, r_max, float(defaults["opinion_grupo_b"]), 0.01,
                             help="En modo bipolar puede ser negativo — rechazo activo.")
    pertenencia = st.slider("Intensidad identidad grupal", 0.0, 1.0, 0.65, 0.01)

    st.markdown("---")
    st.markdown("#### 🔬 Mecanismos avanzados")

    sesgo_conf = st.slider(
        "Sesgo de confirmación",
        0.0, 1.0, 0.3, 0.05,
        help="0 = sin sesgo | 1 = ignora totalmente la información contraria a la posición actual."
    )

    activar_narrativa_b = st.toggle(
        "Activar narrativa competidora (B)",
        value=False,
        help="Habilita el modelo de contagio competitivo: dos narrativas compiten.",
    )
    narrativa_b = 0.0
    if activar_narrativa_b:
        narrativa_b = st.slider(
            "Intensidad narrativa B",
            r_min, r_max,
            -0.3 if es_bipolar else 0.3,
            0.01,
            help="Narrativa rival o contra-narrativa.",
        )

    hk_epsilon = st.slider(
        "Radio de confianza HK (ε)",
        0.1, 0.8, 0.3, 0.05,
        help=(
            "Hegselmann-Krause: solo se escucha a quienes estén a ≤ ε de distancia. "
            "Valores pequeños → más clusters y polarización."
        ),
    )

    homofilia_tasa = st.slider(
        "Tasa de homofilia",
        0.0, 0.2, 0.05, 0.01,
        help="Velocidad con la que los pesos de influencia se ajustan por similitud de opinión.",
    )

    st.markdown("---")
    st.markdown("#### ⚙️ Simulación")

    pasos       = st.slider("Pasos temporales",   20, 300, 60, 5)
    cada_n      = st.slider("LLM cada N pasos",    1,  20,  5, 1)
    alpha       = st.slider("Blend (regla vs base)", 0.0, 1.0, 0.80, 0.05)

    st.markdown("---")
    st.markdown("#### 🎲 Modo probabilístico")
    modo_prob = st.toggle("Activar simulación múltiple", value=False)
    n_sims = 50
    if modo_prob:
        n_sims = st.slider("Número de simulaciones", 10, 200, 50, 10)

    st.markdown("---")
    correr = st.button("▶  Ejecutar simulación")


# ------------------------------------------------------------
# LÓGICA PRINCIPAL
# ------------------------------------------------------------
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
    }

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

    with st.spinner("Simulando..."):
        historial = simular(
            estado_inicial, pasos=pasos, cada_n_pasos=cada_n,
            config=config_run, verbose=False,
        )
        resultado_prob = None
        if modo_prob:
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
    badges.append(
        f'<span class="badge" style="background:#0d1520;color:{color_rango};border:1px solid {color_rango}">'
        f'rango {nombre_rango.split("—")[0].strip()} · neutro={neutro}</span>'
    )
    st.markdown(" ".join(badges), unsafe_allow_html=True)

    # ── MÉTRICAS ───────────────────────────────────────────
    st.markdown("### Resultados")
    c1, c2, c3, c4 = st.columns(4)

    delta_cls = "metric-delta-pos" if delta > 0 else ("metric-delta-neg" if delta < 0 else "metric-delta-neu")
    delta_sym = "▲" if delta > 0.01 else ("▼" if delta < -0.01 else "◆")

    with c1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">Opinión final</div>
            <div class="metric-value">{stats['opinion_final']:+.3f}</div>
            <div class="{delta_cls}">{delta_sym} {delta:+.3f} vs inicio</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        pol     = stats["polarizacion_media"]
        amp     = r_max - r_min
        pol_cls = "metric-delta-neg" if pol > 0.3 * amp else "metric-delta-neu"
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">Polarización media</div>
            <div class="metric-value">{pol:.3f}</div>
            <div class="{pol_cls}">distancia al neutro ({neutro})</div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">Media ± σ</div>
            <div class="metric-value">{stats['media']:+.3f}</div>
            <div class="metric-delta-neu">σ = {stats['desviacion']:.3f}</div>
        </div>""", unsafe_allow_html=True)

    with c4:
        regla_dom     = stats.get("regla_dominante", "—")
        reglas_usadas = [h.get("_regla_nombre", "") for h in historial if "_regla_nombre" in h]
        n_dom         = Counter(reglas_usadas).get(regla_dom, 0)
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">Régimen dominante</div>
            <div class="metric-value" style="font-size:1.0rem">{regla_dom}</div>
            <div class="metric-delta-neu">{n_dom}/{pasos} pasos</div>
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
# ESTADO VACÍO
# ------------------------------------------------------------
else:
    st.markdown("""
    <div style="border:1px dashed #1a2535;border-radius:4px;padding:48px;text-align:center;margin-top:2rem;">
        <div style="font-family:'IBM Plex Mono',monospace;color:#3d5166;font-size:0.8rem;letter-spacing:2px;">
            CONFIGURA LOS PARÁMETROS EN EL PANEL IZQUIERDO<br>Y PRESIONA ▶ EJECUTAR SIMULACIÓN
        </div>
    </div>""", unsafe_allow_html=True)

    with st.expander("📖 Guía de modelos disponibles"):
        st.markdown("""
**Reglas de transición:**

| ID | Nombre | Fundamento | Cuándo domina |
|---|---|---|---|
| 0 | Lineal | Friedkin-Johnsen | Condiciones moderadas |
| 1 | Umbral | Granovetter (simple) | Propaganda cruza punto crítico |
| 2 | Memoria | DeGroot con lag | Sistema estable, inercia |
| 3 | Backlash | Literatura persuasión | Rechazo establecido + propaganda |
| 4 | Polarización | Cámara de eco | Tendencia ya iniciada |
| 5 | **HK** | Hegselmann-Krause (2002) | Grupos muy distantes entre sí |
| 6 | **Contagio competitivo** | Beutel et al. (2012) | Dos narrativas activas |
| 7 | **Umbral heterogéneo** | Granovetter (1978) | Cascadas sociales |
| 8 | **Homofilia** | Axelrod (1997) | Grupos convergen por similitud |

**Mecanismos transversales:**
- **Sesgo de confirmación** — propaganda contraria llega atenuada según la posición actual
- **Rango bipolar [-1,1]** — rechazo activo tiene expresión directa y simétrica con el apoyo
- **Narrativa B** — habilita el contagio competitivo entre dos narrativas simultáneas
        """)

    with st.expander("📖 ¿Qué rango usar?"):
        st.markdown("""
| Situación | Rango | Por qué |
|---|---|---|
| Vacuna, política pública, producto nuevo | **[-1,1] bipolar** | Rechazo activo ≠ indiferencia |
| Elecciones, referéndum | **[-1,1] bipolar** | Votar en contra ≠ abstención |
| Probabilidad de adopción de tecnología | **[0,1] probabilístico** | Tasa de adopción natural |
| Difusión de información / contagio | **[0,1] probabilístico** | Modelos SIR en este rango |
        """)
