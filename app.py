"""
BeyondSight — Interfaz Streamlit
Visualización interactiva del simulador híbrido de dinámica social
"""

import json

import pandas as pd
import streamlit as st

# Import del núcleo — nombre estable, sin versiones
from simulator import (
    resumen_historial,
    simular,
)

# ------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# ------------------------------------------------------------
st.set_page_config(
    page_title="BeyondSight",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------
# ESTILOS — tema oscuro científico, tipografía técnica
# ------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #0a0e14;
    color: #c5cdd9;
}

.stApp { background-color: #0a0e14; }

/* Header principal */
.bs-header {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2.2rem;
    font-weight: 600;
    color: #5ccfe6;
    letter-spacing: -0.5px;
    margin-bottom: 0;
    line-height: 1.1;
}
.bs-subtitle {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    color: #3d5166;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 4px;
    margin-bottom: 2rem;
}

/* Tarjetas de métricas */
.metric-card {
    background: #0d1520;
    border: 1px solid #1a2535;
    border-left: 3px solid #5ccfe6;
    border-radius: 4px;
    padding: 14px 18px;
    margin-bottom: 10px;
}
.metric-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    color: #3d5166;
    text-transform: uppercase;
    letter-spacing: 1.5px;
}
.metric-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.6rem;
    font-weight: 600;
    color: #5ccfe6;
    line-height: 1.2;
}
.metric-delta-pos { color: #bae67e; font-size: 0.85rem; }
.metric-delta-neg { color: #ff8f40; font-size: 0.85rem; }
.metric-delta-neu { color: #3d5166; font-size: 0.85rem; }

/* Sección de reglas */
.regla-badge {
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    padding: 2px 8px;
    border-radius: 2px;
    background: #1a2535;
    color: #5ccfe6;
    border: 1px solid #2a3f58;
    margin: 2px;
}

/* Log entries */
.log-entry {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: #4d6680;
    padding: 3px 0;
    border-bottom: 1px solid #111820;
}
.log-entry:hover { color: #8ba7c0; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #0d1520;
    border-right: 1px solid #1a2535;
}
section[data-testid="stSidebar"] .stSlider > div > div {
    background: #5ccfe6 !important;
}

/* Botón */
.stButton > button {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
    background: #0d1520;
    color: #5ccfe6;
    border: 1px solid #5ccfe6;
    border-radius: 3px;
    padding: 10px 28px;
    letter-spacing: 1px;
    text-transform: uppercase;
    transition: all 0.15s ease;
    width: 100%;
}
.stButton > button:hover {
    background: #5ccfe6;
    color: #0a0e14;
}

/* Expander */
.streamlit-expanderHeader {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    color: #3d5166 !important;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* Ocultar elementos de Streamlit */
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
# SIDEBAR — controles de simulación
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("#### Estado inicial del sistema")

    opinion0 = st.slider("Opinión inicial", 0.0, 1.0, 0.50, 0.01,
                         help="Posición de partida de la opinión media [0=rechazo, 1=apoyo]")
    propaganda = st.slider("Intensidad de propaganda", 0.0, 1.0, 0.70, 0.01,
                           help="Nivel de exposición a mensajes persuasivos")
    confianza = st.slider("Confianza institucional", 0.0, 1.0, 0.40, 0.01,
                          help="Confianza en instituciones — afecta el ruido del sistema")
    tension = st.slider("Tensión social", 0.0, 1.0, 0.30, 0.01)

    st.markdown("---")
    st.markdown("#### Dinámica de grupos")
    op_grupo_a = st.slider("Opinión grupo afín", 0.0, 1.0, 0.72, 0.01,
                           help="Opinión media del grupo social cercano")
    op_grupo_b = st.slider("Opinión grupo contrario", 0.0, 1.0, 0.28, 0.01)
    pertenencia = st.slider("Identidad grupal", 0.0, 1.0, 0.65, 0.01,
                            help="Qué tan fuerte es la presión del grupo afín [0=neutra, 1=total]")

    st.markdown("---")
    st.markdown("#### Parámetros de simulación")
    pasos = st.slider("Pasos temporales", 20, 300, 60, 5)
    cada_n = st.slider("LLM cada N pasos", 1, 20, 5, 1,
                       help="Frecuencia de consulta al LLM selector de reglas")
    alpha = st.slider("Blend (regla LLM vs tendencia base)", 0.0, 1.0, 0.80, 0.05,
                      help="1.0 = solo regla LLM | 0.0 = solo tendencia base")

    st.markdown("---")
    usar_llm = st.toggle("Usar Ollama (LLM real)", value=False,
                         help="Requiere Ollama corriendo en localhost:11434")

    if usar_llm:
        modelo_ollama = st.text_input("Modelo Ollama", value="llama3:8b")
    else:
        modelo_ollama = "llama3:8b"
        st.caption("🔁 Modo heurístico activo — sin Ollama")

    st.markdown("---")
    correr = st.button("▶  Ejecutar simulación")


# ------------------------------------------------------------
# LÓGICA PRINCIPAL
# ------------------------------------------------------------

if "historial" not in st.session_state:
    st.session_state["historial"] = None
if "stats" not in st.session_state:
    st.session_state["stats"] = None
if "estado_inicial" not in st.session_state:
    st.session_state["estado_inicial"] = None
if "op_grupo_a" not in st.session_state:
    st.session_state["op_grupo_a"] = None
if "op_grupo_b" not in st.session_state:
    st.session_state["op_grupo_b"] = None
if "pasos" not in st.session_state:
    st.session_state["pasos"] = None
if "cada_n" not in st.session_state:
    st.session_state["cada_n"] = None

if correr:
    estado_inicial = {
        "opinion": opinion0,
        "propaganda": propaganda,
        "confianza": confianza,
        "tension": tension,
        "opinion_grupo_a": op_grupo_a,
        "opinion_grupo_b": op_grupo_b,
        "pertenencia_grupo": pertenencia,
    }

    config_override = {
        "alpha_blend": alpha,
        "ollama_model": modelo_ollama,
    }

    with st.spinner("Simulando..."):
        historial = simular(
            estado_inicial,
            escenario="campana",
            pasos=pasos,
            cada_n_pasos=cada_n,
            usar_llm_real=usar_llm,
            config=config_override,
            verbose=False,
        )

    st.session_state["historial"] = historial
    st.session_state["stats"] = resumen_historial(historial)
    st.session_state["estado_inicial"] = estado_inicial
    st.session_state["op_grupo_a"] = op_grupo_a
    st.session_state["op_grupo_b"] = op_grupo_b
    st.session_state["pasos"] = pasos
    st.session_state["cada_n"] = cada_n

if st.session_state["historial"] is not None:
    historial = st.session_state["historial"]
    stats = st.session_state["stats"]
    estado_inicial = st.session_state["estado_inicial"]
    op_grupo_a = st.session_state["op_grupo_a"]
    op_grupo_b = st.session_state["op_grupo_b"]
    pasos = st.session_state["pasos"]
    cada_n = st.session_state["cada_n"]

    opiniones = [h["opinion"] for h in historial]
    delta = stats["delta_total"]
    delta_cls = "metric-delta-pos" if delta > 0.02 else ("metric-delta-neg" if delta < -0.02 else "metric-delta-neu")
    delta_sym = "▲" if delta > 0.02 else ("▼" if delta < -0.02 else "◆")

    # --- Métricas superiores ---
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Opinión final</div>
            <div class="metric-value">{stats['opinion_final']:.3f}</div>
            <div class="{delta_cls}">{delta_sym} {delta:+.3f} vs inicio</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Media trayectoria</div>
            <div class="metric-value">{stats['media']:.3f}</div>
            <div class="metric-delta-neu">σ = {stats['desviacion']:.3f}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Rango</div>
            <div class="metric-value">{stats['maximo'] - stats['minimo']:.3f}</div>
            <div class="metric-delta-neu">[{stats['minimo']:.3f} – {stats['maximo']:.3f}]</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        # Regla más usada
        reglas_usadas = [h.get("_regla_nombre", "lineal") for h in historial[1:]]
        from collections import Counter
        regla_dominante = Counter(reglas_usadas).most_common(1)[0][0]
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Régimen dominante</div>
            <div class="metric-value" style="font-size:1.1rem">{regla_dominante}</div>
            <div class="metric-delta-neu">{Counter(reglas_usadas).most_common(1)[0][1]}/{pasos} pasos</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Gráfico principal ---
    col_main, col_side = st.columns([3, 1])

    with col_main:
        df = pd.DataFrame({
            "Opinión": opiniones,
            "Propaganda": [estado_inicial["propaganda"]] * len(opiniones),
            "Grupo afín": [op_grupo_a] * len(opiniones),
            "Grupo contrario": [op_grupo_b] * len(opiniones),
        })
        st.markdown("**Trayectoria de opinión**")
        st.line_chart(df, color=["#5ccfe6", "#ff8f40", "#bae67e", "#f28779"])

    with col_side:
        st.markdown("**Distribución de reglas**")
        from collections import Counter
        conteo = Counter(reglas_usadas)
        df_reglas = pd.DataFrame({
            "Regla": list(conteo.keys()),
            "Pasos": list(conteo.values()),
        }).sort_values("Pasos", ascending=False)
        st.dataframe(df_reglas, use_container_width=True, hide_index=True)

    # --- Log de decisiones del LLM ---
    with st.expander("Log de decisiones del LLM selector"):
        cambios = [h for h in historial[1:] if h.get("_paso", 0) % cada_n == 0]
        for h in cambios:
            razon = h.get("_razon", "")
            regla = h.get("_regla_nombre", "?")
            paso = h.get("_paso", "?")
            opinion = h.get("opinion", 0)
            st.markdown(
                f'<div class="log-entry">t={paso:3d} │ <b>{regla}</b> │ '
                f'op={opinion:.3f} │ {razon}</div>',
                unsafe_allow_html=True,
            )

    # --- Exportar datos ---
    with st.expander("Exportar historial"):
        df_export = pd.DataFrame(historial)
        cols_export = ["opinion", "propaganda", "confianza", "_paso", "_regla_nombre", "_razon"]
        cols_presentes = [c for c in cols_export if c in df_export.columns]
        st.dataframe(df_export[cols_presentes], use_container_width=True)

        csv = df_export[cols_presentes].to_csv(index=False)
        st.download_button(
            "⬇ Descargar CSV",
            data=csv,
            file_name="beyondsight_historial.csv",
            mime="text/csv",
        )
        st.download_button(
            "⬇ Descargar JSON",
            data=json.dumps(historial, indent=2, default=str),
            file_name="beyondsight_historial.json",
            mime="application/json",
        )

else:
    # Estado vacío — instrucciones
    st.markdown("""
    <div style="
        border: 1px dashed #1a2535;
        border-radius: 4px;
        padding: 48px;
        text-align: center;
        margin-top: 2rem;
    ">
        <div style="font-family:'IBM Plex Mono',monospace; color:#3d5166; font-size:0.8rem; letter-spacing:2px;">
            CONFIGURA LOS PARÁMETROS EN EL PANEL IZQUIERDO<br>Y PRESIONA ▶ EJECUTAR SIMULACIÓN
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Documentación rápida del sistema"):
        st.markdown("""
**BeyondSight** es un simulador híbrido de dinámica social que combina:

- **Núcleo numérico** — ecuaciones de transición de estado (lineal, umbral, memoria, backlash, polarización)
- **LLM como selector de régimen** — elige qué ecuación aplicar según el contexto y la trayectoria reciente
- **Modelo de dos grupos** — captura presión social y polarización (reemplaza el proxy naive de vecinos)

**Variables principales:**
- `opinion` — posición media del sistema [0=rechazo total, 1=apoyo total]
- `propaganda` — intensidad de exposición a mensajes persuasivos
- `confianza` — confianza institucional (afecta la volatilidad del sistema)
- `grupos A/B` — opiniones de los grupos afín y contrario

**Reglas de transición:**
| Regla | Cuándo domina |
|---|---|
| Lineal | Condiciones moderadas, sin efectos extremos |
| Umbral | Propaganda alta cruza punto crítico |
| Memoria | Sistema estable, inercia dominante |
| Backlash | Opinión baja + propaganda alta = rechazo |
| Polarización | Tendencia ya iniciada, efecto cámara de eco |

**Para usar con Ollama:** instala [Ollama](https://ollama.ai), ejecuta `ollama serve` y activa el toggle en el sidebar.
        """)
