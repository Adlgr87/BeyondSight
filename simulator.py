"""
BeyondSight — Simulador híbrido de dinámica social
Núcleo numérico + LLM como selector de régimen dinámico

Modelos integrados:
  REGLAS BASE (originales):
    0: lineal       — cambio proporcional suave
    1: umbral       — salto al cruzar punto crítico
    2: memoria      — inercia del estado pasado
    3: backlash     — propaganda refuerza posición contraria
    4: polarizacion — aleja la opinión del neutro (cámara de eco)

  MODELOS NUEVOS:
    5: hk           — Hegselmann-Krause: confianza acotada, formación natural de clusters
    6: contagio_competitivo — dos narrativas compitiendo simultáneamente
    7: umbral_heterogeneo   — distribución de umbrales (Granovetter), cascadas sociales
    8: homofilia    — red co-evolutiva: los pesos de influencia cambian con la opinión

  MECANISMOS TRANSVERSALES (se aplican a todas las reglas):
    · sesgo_confirmacion  — propaganda contraria pierde peso según posición actual
    · homofilia dinámica  — actualiza pesos de grupos en cada paso

RANGOS DE OPINIÓN:
  [0, 1] — Probabilístico. Neutro=0.5
  [-1, 1] — Bipolar. Neutro=0.0. Rechazo activo ≠ indiferencia.

PROVEEDORES LLM:
  heurístico | ollama | groq | openai | openrouter

Autor: BeyondSight Research
"""

import json
import logging
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import requests

# ------------------------------------------------------------
# LOGGING
# ------------------------------------------------------------
LOG_PATH = Path("beyondsight_run.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("beyondsight")


# ------------------------------------------------------------
# RANGOS DE OPINIÓN
# ------------------------------------------------------------
RANGOS_DISPONIBLES: dict[str, dict] = {
    "[0, 1] — Probabilístico": {
        "min": 0.0, "max": 1.0, "neutro": 0.5,
        "descripcion": "Opinión como probabilidad de apoyo. Neutro=0.5. Modelos SIR, adopción.",
        "ejemplo_apoyo": 0.8, "ejemplo_rechazo": 0.2, "ejemplo_neutro": 0.5,
        "defaults": {
            "opinion_inicial": 0.50, "propaganda": 0.70, "confianza": 0.40,
            "opinion_grupo_a": 0.72, "opinion_grupo_b": 0.28,
        },
    },
    "[-1, 1] — Bipolar": {
        "min": -1.0, "max": 1.0, "neutro": 0.0,
        "descripcion": "Rechazo activo en negativo. Neutro=0. Polarización, campañas, elecciones.",
        "ejemplo_apoyo": 0.7, "ejemplo_rechazo": -0.7, "ejemplo_neutro": 0.0,
        "defaults": {
            "opinion_inicial": 0.00, "propaganda": 0.40, "confianza": 0.40,
            "opinion_grupo_a": 0.65, "opinion_grupo_b": -0.55,
        },
    },
}

# ------------------------------------------------------------
# PROVEEDORES LLM
# ------------------------------------------------------------
PROVEEDORES: dict[str, dict] = {
    "heurístico": {
        "descripcion": "Sin LLM — lógica determinista, sin costo ni API key",
        "requiere_key": False, "base_url": None,
        "modelos_sugeridos": ["(ninguno)"],
    },
    "ollama": {
        "descripcion": "LLM local con Ollama — privado, sin costo por llamada",
        "requiere_key": False, "base_url": "http://localhost:11434",
        "modelos_sugeridos": ["llama3:8b", "mistral:7b", "phi3:mini", "gemma2:2b"],
    },
    "groq": {
        "descripcion": "Groq Cloud — muy rápido, tier gratuito generoso",
        "requiere_key": True, "base_url": "https://api.groq.com/openai/v1",
        "modelos_sugeridos": [
            "llama-3.1-8b-instant", "llama-3.3-70b-versatile",
            "meta-llama/llama-4-scout-17b-16e-instruct",
        ],
    },
    "openai": {
        "descripcion": "OpenAI API — GPT-4o, GPT-4o-mini, etc.",
        "requiere_key": True, "base_url": "https://api.openai.com/v1",
        "modelos_sugeridos": ["gpt-4o-mini", "gpt-4o", "gpt-4.1-nano"],
    },
    "openrouter": {
        "descripcion": "OpenRouter — acceso a cientos de modelos con una sola key",
        "requiere_key": True, "base_url": "https://openrouter.ai/api/v1",
        "modelos_sugeridos": [
            "meta-llama/llama-3.3-70b-instruct",
            "google/gemini-flash-1.5",
            "mistralai/mistral-7b-instruct",
        ],
    },
}

# ------------------------------------------------------------
# CONFIGURACIÓN POR DEFECTO
# ------------------------------------------------------------
DEFAULT_CONFIG: dict[str, Any] = {
    # Rango
    "rango": "[0, 1] — Probabilístico",
    # LLM
    "proveedor": "heurístico",
    "modelo": "",
    "api_key": "",
    "ollama_host": "http://localhost:11434",
    "llm_timeout": 20,
    "llm_temperature": 0.0,
    # Motor
    "alpha_blend": 0.8,
    "ruido_base": 0.03,
    "ruido_desconfianza": 0.08,
    "efecto_vecinos_peso": 0.05,
    "ventana_historial_llm": 6,
    # Simulación múltiple
    "ruido_estado_inicial": 0.01,
    # ── Nuevos mecanismos ──────────────────────────────────
    # Sesgo de confirmación: propaganda contraria pierde peso
    # 0.0 = sin sesgo | 1.0 = sesgo total (ignora información contraria)
    "sesgo_confirmacion": 0.3,
    # HK — Confianza Acotada
    # Solo se escucha a quienes están a ≤ epsilon de distancia
    "hk_epsilon": 0.3,
    # Contagio Competitivo
    # Peso de la narrativa B al competir con la A
    "competencia_peso": 0.4,
    # Umbral Heterogéneo (Granovetter)
    # Media y std de la distribución de umbrales individuales
    "umbral_media": 0.5,
    "umbral_std":   0.15,
    # Homofilia dinámica
    # Velocidad con la que los pesos de grupo se actualizan según similitud de opinión
    "homofilia_tasa": 0.05,
}

# Rangos válidos de parámetros del LLM
_RANGOS_PARAMS: dict[str, dict[str, tuple]] = {
    "lineal":               {"a": (0.5, 0.9), "b": (0.1, 0.5)},
    "umbral":               {"umbral": (0.3, 0.8), "incremento": (0.05, 0.3)},
    "memoria":              {"alpha": (0.5, 0.8), "beta": (0.1, 0.3), "gamma": (0.05, 0.2)},
    "backlash":             {"penalizacion": (0.05, 0.3)},
    "polarizacion":         {"fuerza": (0.05, 0.25)},
    "hk":                   {"epsilon": (0.1, 0.6)},
    "contagio_competitivo": {"competencia": (0.2, 0.7)},
    "umbral_heterogeneo":   {"media": (0.3, 0.7), "std": (0.05, 0.25)},
    "homofilia":            {"tasa": (0.02, 0.15)},
}


# ============================================================
# HELPERS DE RANGO
# Toda la lógica de rango pasa por aquí — motor agnóstico al rango.
# ============================================================

def _get_rango(cfg: dict) -> dict:
    nombre = cfg.get("rango", "[0, 1] — Probabilístico")
    return RANGOS_DISPONIBLES.get(nombre, RANGOS_DISPONIBLES["[0, 1] — Probabilístico"])

def _clip(val: float, cfg: dict) -> float:
    r = _get_rango(cfg)
    return float(np.clip(val, r["min"], r["max"]))

def _neutro(cfg: dict) -> float:
    return _get_rango(cfg)["neutro"]

def _es_bipolar(cfg: dict) -> bool:
    return _get_rango(cfg)["min"] < 0

def _amplitud(cfg: dict) -> float:
    r = _get_rango(cfg)
    return r["max"] - r["min"]


# ============================================================
# MECANISMO: SESGO DE CONFIRMACIÓN
# Transversal — se aplica antes de pasar la propaganda a cualquier regla.
# Referencia: Sunstein (2009), Nickerson (1998).
# ============================================================

def _aplicar_sesgo_confirmacion(propaganda: float, opinion: float,
                                 cfg: dict) -> float:
    """
    Reduce el peso de información contraria a la posición actual.

    Si propaganda y opinión apuntan en la misma dirección desde el neutro
    → propaganda llega con peso completo.
    Si van en direcciones opuestas
    → propaganda se atenúa según sesgo_confirmacion ∈ [0, 1].

    Parámetro: cfg["sesgo_confirmacion"]
      0.0 = sin sesgo (modelo clásico)
      1.0 = sesgo total (información contraria completamente ignorada)
    """
    sesgo   = float(np.clip(cfg.get("sesgo_confirmacion", 0.0), 0.0, 1.0))
    neutro  = _neutro(cfg)

    if sesgo == 0.0:
        return propaganda

    # Detectar si van en direcciones opuestas desde el neutro
    misma_dir = (opinion - neutro) * (propaganda - neutro) >= 0
    if misma_dir:
        return propaganda
    else:
        # Atenuación proporcional al sesgo
        return propaganda * (1.0 - sesgo)


# ============================================================
# MECANISMO: HOMOFILIA DINÁMICA
# La fuerza de influencia de cada grupo se ajusta según similitud de opinión.
# Referencia: Axelrod (1997), Flache et al. (2017).
# ============================================================

def _actualizar_pesos_homofilia(estado: dict, cfg: dict) -> tuple[float, float]:
    """
    Calcula nuevos pesos de influencia para grupos A y B basados en
    la similitud de opinión con el estado actual.

    Cuanto más similar la opinión de un grupo a la del sistema,
    mayor influencia recibe (homofilia positiva).

    Retorna: (peso_grupo_a, peso_grupo_b) normalizados a suma=1
    """
    tasa     = float(np.clip(cfg.get("homofilia_tasa", 0.05), 0.0, 0.3))
    opinion  = estado["opinion"]
    op_a     = estado.get("opinion_grupo_a", 0.7)
    op_b     = estado.get("opinion_grupo_b", 0.3)
    perten   = estado.get("pertenencia_grupo", 0.6)

    # Similitud = 1 - distancia normalizada al rango
    amp      = _amplitud(cfg)
    sim_a    = 1.0 - abs(opinion - op_a) / amp
    sim_b    = 1.0 - abs(opinion - op_b) / amp

    # Actualizar pertenencia hacia el grupo más similar
    nuevo_perten = perten + tasa * (sim_a - sim_b)
    nuevo_perten = float(np.clip(nuevo_perten, 0.1, 0.9))
    return nuevo_perten


# ============================================================
# REGLAS DE TRANSICIÓN — ORIGINALES (mejoradas con rango dual)
# ============================================================

def regla_lineal(estado: dict, params: dict, cfg: dict) -> dict:
    """
    Cambio proporcional a opinión y propaganda.
    En [-1,1]: propaganda negativa genera rechazo activo.
    """
    a, b  = params.get("a", 0.7), params.get("b", 0.3)
    prop  = _aplicar_sesgo_confirmacion(estado["propaganda"], estado["opinion"], cfg)
    nuevo = estado.copy()
    nuevo["opinion"] = _clip(a * estado["opinion"] + b * prop, cfg)
    return nuevo


def regla_umbral(estado: dict, params: dict, cfg: dict) -> dict:
    """
    Salto no lineal cuando la propaganda supera un umbral crítico.
    En [-1,1]: considera dirección de la propaganda.
    """
    r          = _get_rango(cfg)
    umbral     = params.get("umbral", 0.65 if not _es_bipolar(cfg) else 0.4)
    incremento = params.get("incremento", 0.15)
    prop       = _aplicar_sesgo_confirmacion(estado["propaganda"], estado["opinion"], cfg)
    nuevo = estado.copy()
    if abs(prop) > abs(umbral):
        signo = np.sign(prop) if _es_bipolar(cfg) else 1.0
        val   = estado["opinion"] + signo * incremento * (r["max"] - abs(estado["opinion"]))
    else:
        val = estado["opinion"]
    nuevo["opinion"] = _clip(val, cfg)
    return nuevo


def regla_memoria(estado: dict, params: dict, cfg: dict) -> dict:
    """Inercia: el estado presente depende del estado anterior."""
    alpha = params.get("alpha", 0.7)
    beta  = params.get("beta",  0.2)
    gamma = params.get("gamma", 0.1)
    prev  = estado.get("opinion_prev", estado["opinion"])
    prop  = _aplicar_sesgo_confirmacion(estado["propaganda"], estado["opinion"], cfg)
    nuevo = estado.copy()
    nuevo["opinion"] = _clip(
        alpha * estado["opinion"] + beta * prev + gamma * prop, cfg
    )
    return nuevo


def regla_backlash(estado: dict, params: dict, cfg: dict) -> dict:
    """
    La propaganda refuerza la posición contraria cuando hay rechazo establecido.
    [0,1]: activa cuando opinion < umbral_inferior.
    [-1,1]: activa cuando opinion < neutro.
    """
    penalizacion = params.get("penalizacion", 0.15)
    prop         = _aplicar_sesgo_confirmacion(estado["propaganda"], estado["opinion"], cfg)
    nuevo = estado.copy()
    neutro = _neutro(cfg)
    if _es_bipolar(cfg):
        if estado["opinion"] < neutro:
            val = estado["opinion"] - penalizacion * abs(prop)
        else:
            val = estado["opinion"]
    else:
        umbral_inf = params.get("umbral_inferior", 0.35)
        if estado["opinion"] < umbral_inf:
            val = estado["opinion"] - penalizacion * prop
        else:
            val = estado["opinion"]
    nuevo["opinion"] = _clip(val, cfg)
    return nuevo


def regla_polarizacion(estado: dict, params: dict, cfg: dict) -> dict:
    """
    Aleja la opinión del neutro — efecto cámara de eco.
    Funciona en ambos rangos usando el neutro del rango activo.
    """
    fuerza  = params.get("fuerza", 0.1)
    opinion = estado["opinion"]
    neutro  = _neutro(cfg)
    r       = _get_rango(cfg)
    nuevo   = estado.copy()
    if opinion >= neutro:
        val = opinion + fuerza * (r["max"] - opinion)
    else:
        val = opinion - fuerza * (opinion - r["min"])
    nuevo["opinion"] = _clip(val, cfg)
    return nuevo


# ============================================================
# REGLA NUEVA 1: HEGSELMANN-KRAUSE (Confianza Acotada)
# Solo se escucha a quienes están dentro de epsilon de distancia.
# Genera clustering y polarización de forma emergente.
# Referencia: Hegselmann & Krause (2002).
# ============================================================

def regla_hk(estado: dict, params: dict, cfg: dict) -> dict:
    """
    Modelo de Hegselmann-Krause: confianza acotada.

    El agente solo es influenciado por grupos cuya opinión esté
    dentro de epsilon de la propia. Si ningún grupo está dentro
    del radio, la opinión no cambia (fragmentación emergente).

    Parámetro: epsilon (radio de confianza) ∈ [0.1, 0.6]
    Cuanto más pequeño epsilon, más clusters y polarización.
    """
    epsilon = params.get("epsilon", cfg.get("hk_epsilon", 0.3))
    opinion = estado["opinion"]
    op_a    = estado.get("opinion_grupo_a", _get_rango(cfg)["ejemplo_apoyo"])
    op_b    = estado.get("opinion_grupo_b", _get_rango(cfg)["ejemplo_rechazo"])
    perten  = estado.get("pertenencia_grupo", 0.6)
    prop    = _aplicar_sesgo_confirmacion(estado["propaganda"], opinion, cfg)

    # Determinar qué grupos están dentro del radio de confianza
    grupos_validos = []
    pesos_validos  = []

    if abs(opinion - op_a) <= epsilon:
        grupos_validos.append(op_a)
        pesos_validos.append(perten)

    if abs(opinion - op_b) <= epsilon:
        grupos_validos.append(op_b)
        pesos_validos.append(1.0 - perten)

    nuevo = estado.copy()
    if grupos_validos:
        # Promedio ponderado solo de grupos dentro del radio
        total_peso   = sum(pesos_validos)
        opinion_ref  = sum(g * p for g, p in zip(grupos_validos, pesos_validos)) / total_peso
        # Convergencia gradual hacia la referencia de confianza
        alpha        = params.get("alpha", 0.3)
        val          = opinion + alpha * (opinion_ref - opinion) + 0.05 * prop
    else:
        # Nadie dentro del radio → fragmentación, opinión casi estática
        val = opinion + 0.01 * prop  # influencia mínima de propaganda

    nuevo["opinion"] = _clip(val, cfg)
    return nuevo


# ============================================================
# REGLA NUEVA 2: CONTAGIO COMPETITIVO
# Dos narrativas compiten simultáneamente.
# La narrativa B frena el avance de la narrativa A.
# Referencia: Beutel et al. (2012), Gleeson et al. (2014).
# ============================================================

def regla_contagio_competitivo(estado: dict, params: dict, cfg: dict) -> dict:
    """
    Modela la competencia entre dos narrativas simultáneas.

    narrativa_a = propaganda principal (estado["propaganda"])
    narrativa_b = contra-narrativa o narrativa rival (estado["narrativa_b"])

    La adopción de A se frena en proporción a la fuerza de B.
    En modo bipolar: propaganda negativa ya funciona como narrativa B,
    pero este modelo lo hace explícito y simétrico.

    Parámetro: competencia ∈ [0.2, 0.7] — peso de la narrativa B
    """
    competencia  = params.get("competencia", cfg.get("competencia_peso", 0.4))
    opinion      = estado["opinion"]
    narrativa_a  = _aplicar_sesgo_confirmacion(estado["propaganda"], opinion, cfg)
    # narrativa_b puede estar en el estado o inferirse como la opuesta
    narrativa_b  = estado.get("narrativa_b", -narrativa_a if _es_bipolar(cfg) else 1.0 - narrativa_a)

    # Influencia neta: A gana si es más fuerte que B
    influencia_neta = narrativa_a - competencia * narrativa_b
    neutro          = _neutro(cfg)

    # La influencia neta empuja la opinión hacia o desde el neutro
    nuevo = estado.copy()
    val   = opinion + 0.15 * influencia_neta * (1.0 - abs(opinion - neutro) / _amplitud(cfg))
    nuevo["opinion"] = _clip(val, cfg)
    return nuevo


# ============================================================
# REGLA NUEVA 3: UMBRAL HETEROGÉNEO (Granovetter)
# Cada "agente" tiene su propio umbral de adopción.
# La distribución de umbrales genera cascadas sociales.
# Referencia: Granovetter (1978).
# ============================================================

def regla_umbral_heterogeneo(estado: dict, params: dict, cfg: dict) -> dict:
    """
    Modelo de umbral de Granovetter con distribución heterogénea.

    En lugar de un umbral único, la población tiene umbrales distribuidos
    normalmente (media, std). La fracción de la población que ya superó
    su umbral determina si se activa la siguiente ola de adopción.

    Esto genera dinámicas de cascada: pequeños cambios iniciales pueden
    desencadenar adopciones masivas si la distribución es adecuada.

    Parámetros:
      media ∈ [0.3, 0.7] — umbral promedio de la población
      std   ∈ [0.05, 0.25] — dispersión de umbrales (más std = más cascadas)
    """
    media   = params.get("media", cfg.get("umbral_media", 0.5))
    std     = params.get("std",   cfg.get("umbral_std",   0.15))
    opinion = estado["opinion"]
    neutro  = _neutro(cfg)
    prop    = _aplicar_sesgo_confirmacion(estado["propaganda"], opinion, cfg)

    # Fracción de la población que ya superó su umbral personal
    # (modelado con CDF de la normal)
    from scipy.special import erf
    fraccion_adoptantes = 0.5 * (1 + erf((opinion - neutro - media + 0.5) / (std * np.sqrt(2))))
    fraccion_adoptantes = float(np.clip(fraccion_adoptantes, 0.0, 1.0))

    # La fracción de adoptantes genera presión social adicional
    r    = _get_rango(cfg)
    val  = opinion + 0.2 * fraccion_adoptantes * (r["max"] - opinion) + 0.05 * prop

    nuevo = estado.copy()
    nuevo["opinion"] = _clip(val, cfg)
    # Guardar fracción para análisis
    nuevo["_fraccion_adoptantes"] = round(fraccion_adoptantes, 3)
    return nuevo


# ============================================================
# REGLA NUEVA 4: HOMOFILIA (Red Co-evolutiva)
# Los pesos de influencia de los grupos cambian con la opinión.
# Cuanto más similar la opinión de un grupo, más influye.
# Referencia: Axelrod (1997), Centola et al. (2007).
# ============================================================

def regla_homofilia(estado: dict, params: dict, cfg: dict) -> dict:
    """
    Modelo de red co-evolutiva: opinión y estructura se co-influencian.

    En cada paso:
    1. La pertenencia al grupo se actualiza según similitud de opinión
       (quienes piensan igual, influyen más — homofilia).
    2. La nueva estructura de influencia determina el cambio de opinión.

    Esto genera cámaras de eco de forma endógena: sin configurarlo
    explícitamente, el sistema naturalmente se polariza en grupos
    con alta coherencia interna.

    Parámetro: tasa ∈ [0.02, 0.15] — velocidad de actualización de pesos
    """
    tasa    = params.get("tasa", cfg.get("homofilia_tasa", 0.05))
    opinion = estado["opinion"]
    op_a    = estado.get("opinion_grupo_a", _get_rango(cfg)["ejemplo_apoyo"])
    op_b    = estado.get("opinion_grupo_b", _get_rango(cfg)["ejemplo_rechazo"])
    perten  = estado.get("pertenencia_grupo", 0.6)
    prop    = _aplicar_sesgo_confirmacion(estado["propaganda"], opinion, cfg)

    amp    = _amplitud(cfg)
    # Similitud normalizada al rango
    sim_a  = 1.0 - abs(opinion - op_a) / amp
    sim_b  = 1.0 - abs(opinion - op_b) / amp

    # Actualizar pertenencia según similitud (homofilia)
    nuevo_perten = float(np.clip(perten + tasa * (sim_a - sim_b), 0.1, 0.9))

    # Calcular referencia social con nuevos pesos
    ref_social   = nuevo_perten * op_a + (1.0 - nuevo_perten) * op_b
    peso_social  = cfg.get("efecto_vecinos_peso", 0.05)

    val  = opinion + peso_social * (ref_social - opinion) + 0.08 * prop

    nuevo = estado.copy()
    nuevo["opinion"]           = _clip(val, cfg)
    nuevo["pertenencia_grupo"] = nuevo_perten  # persiste al próximo paso
    nuevo["_sim_grupo_a"]      = round(sim_a, 3)
    nuevo["_sim_grupo_b"]      = round(sim_b, 3)
    return nuevo


# ============================================================
# REGISTRO DE REGLAS
# ============================================================

REGLAS: dict[str, dict[int, Any]] = {
    "campana": {
        0: regla_lineal,
        1: regla_umbral,
        2: regla_memoria,
        3: regla_backlash,
        4: regla_polarizacion,
        5: regla_hk,
        6: regla_contagio_competitivo,
        7: regla_umbral_heterogeneo,
        8: regla_homofilia,
    }
}

NOMBRES_REGLAS = {
    0: "lineal",
    1: "umbral",
    2: "memoria",
    3: "backlash",
    4: "polarizacion",
    5: "hk",
    6: "contagio_competitivo",
    7: "umbral_heterogeneo",
    8: "homofilia",
}

# Descripción de cada regla para la UI
DESCRIPCIONES_REGLAS = {
    0: "Cambio proporcional suave",
    1: "Salto al cruzar punto crítico",
    2: "Inercia del estado pasado",
    3: "Propaganda refuerza posición contraria",
    4: "Aleja del neutro (cámara de eco)",
    5: "Confianza acotada — solo escucha a similares (Hegselmann-Krause)",
    6: "Dos narrativas compiten simultáneamente",
    7: "Distribución de umbrales — cascadas sociales (Granovetter)",
    8: "Red co-evolutiva — homofilia dinámica",
}


# ============================================================
# VALIDADOR DE PARÁMETROS LLM
# ============================================================

def _validar_params(regla_nombre: str, params: dict) -> dict:
    rangos = _RANGOS_PARAMS.get(regla_nombre, {})
    return {
        k: float(np.clip(v, *rangos[k])) if k in rangos and isinstance(v, (int, float)) else v
        for k, v in params.items()
    }


# ============================================================
# CONSTRUCCIÓN DEL PROMPT — consciente del rango y nuevas reglas
# ============================================================

def _construir_prompt(estado: dict, escenario: str,
                      historial_reciente: list[dict], cfg: dict) -> str:
    es_bipolar = _es_bipolar(cfg)
    tendencia  = [round(h["opinion"], 3) for h in historial_reciente]
    delta      = round(tendencia[-1] - tendencia[0], 3) if len(tendencia) > 1 else 0.0
    direccion  = "subiendo" if delta > 0.02 else ("bajando" if delta < -0.02 else "estable")

    estado_fmt = {
        k: round(v, 3) if isinstance(v, float) else v
        for k, v in estado.items() if not k.startswith("_")
    }

    rango_desc = (
        "[-1, 1]: 0=neutro, negativo=rechazo activo, positivo=apoyo"
        if es_bipolar else
        "[0, 1]: 0.5=neutro, 0=rechazo total, 1=apoyo total"
    )

    ejemplos = """
Ejemplos de decisión:
- opinion cerca del neutro, propaganda baja, sistema estable → memoria
- propaganda intensa cruza umbral, sistema se mueve → umbral
- grupos muy distantes entre sí → hk (confianza acotada)
- rechazo establecido + propaganda activa → backlash
- dos narrativas activas y tensas → contagio_competitivo
- tendencia fuerte ya iniciada → polarizacion
- se busca efecto de cascada social → umbral_heterogeneo
- grupos tienden a agruparse por similitud → homofilia"""

    return f"""Eres un selector de reglas para simulación de dinámica social.
Escenario: {escenario} | Rango: {rango_desc}

Estado:
{json.dumps(estado_fmt, ensure_ascii=False)}

Tendencia opinión (últimos {len(tendencia)} pasos): {tendencia}
Dirección: {direccion} (Δ={delta:+.3f})
{ejemplos}

Reglas disponibles:
0: lineal               — cambio proporcional suave
1: umbral               — salto al cruzar punto crítico
2: memoria              — inercia del estado pasado
3: backlash             — propaganda refuerza posición contraria
4: polarizacion         — aleja del neutro (cámara de eco)
5: hk                   — confianza acotada, solo escucha a similares
6: contagio_competitivo — dos narrativas compiten simultáneamente
7: umbral_heterogeneo   — cascadas sociales (Granovetter)
8: homofilia            — red co-evolutiva, grupos por similitud

Responde SOLO con JSON:
{{"regla": <0-8>, "params": {{...}}, "razon": "<explicacion>"}}
Fallback: {{"regla": 0, "params": {{}}, "razon": "fallback"}}
"""


# ============================================================
# CAPA LLM
# ============================================================

def _extraer_json(texto: str) -> dict | None:
    inicio = texto.find("{")
    fin    = texto.rfind("}") + 1
    if inicio == -1 or fin == 0:
        return None
    try:
        return json.loads(texto[inicio:fin])
    except json.JSONDecodeError:
        return None


def _llamar_openai_compatible(prompt: str, base_url: str, api_key: str,
                               modelo: str, cfg: dict) -> dict | None:
    try:
        resp = requests.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": modelo,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": cfg["llm_temperature"],
                "max_tokens": 300,
            },
            timeout=cfg["llm_timeout"],
        )
        resp.raise_for_status()
        return _extraer_json(resp.json()["choices"][0]["message"]["content"])
    except requests.exceptions.ConnectionError:
        log.error(f"No se pudo conectar a {base_url}.")
    except requests.exceptions.Timeout:
        log.warning(f"Timeout ({cfg['llm_timeout']}s) en {base_url}.")
    except (KeyError, IndexError) as e:
        log.warning(f"Error parseando respuesta: {e}")
    return None


def _llamar_ollama(prompt: str, cfg: dict) -> dict | None:
    try:
        resp = requests.post(
            f"{cfg['ollama_host']}/api/generate",
            json={
                "model":   cfg["modelo"],
                "prompt":  prompt,
                "stream":  False,
                "options": {"temperature": cfg["llm_temperature"]},
            },
            timeout=cfg["llm_timeout"],
        )
        resp.raise_for_status()
        return _extraer_json(resp.json().get("response", ""))
    except requests.exceptions.ConnectionError:
        log.error("Ollama no responde. → ollama serve")
    except requests.exceptions.Timeout:
        log.warning(f"Timeout ({cfg['llm_timeout']}s) en Ollama.")
    except KeyError as e:
        log.warning(f"Error parseando Ollama: {e}")
    return None


def llamar_llm(estado: dict, escenario: str,
               historial_reciente: list[dict], cfg: dict) -> dict:
    """Dispatcher principal. Siempre retorna un dict válido."""
    proveedor = cfg.get("proveedor", "heurístico")

    if proveedor == "heurístico":
        return llamar_llm_heuristico(estado, escenario, historial_reciente, cfg)

    prompt = _construir_prompt(estado, escenario, historial_reciente, cfg)
    data   = None

    if proveedor == "ollama":
        data = _llamar_ollama(prompt, cfg)
    elif proveedor in PROVEEDORES:
        info    = PROVEEDORES[proveedor]
        api_key = cfg.get("api_key", "").strip()
        modelo  = cfg.get("modelo", "").strip() or info["modelos_sugeridos"][0]
        if not api_key:
            log.error(f"'{proveedor}' requiere API key. → heurístico.")
            return llamar_llm_heuristico(estado, escenario, historial_reciente, cfg)
        data = _llamar_openai_compatible(prompt, info["base_url"], api_key, modelo, cfg)
    else:
        log.error(f"Proveedor desconocido: '{proveedor}'. → heurístico.")
        return llamar_llm_heuristico(estado, escenario, historial_reciente, cfg)

    if data is None:
        log.warning("LLM sin respuesta → heurístico.")
        return llamar_llm_heuristico(estado, escenario, historial_reciente, cfg)

    regla_id = int(data.get("regla", 0))
    if regla_id not in REGLAS.get(escenario, {}):
        log.warning(f"Regla inválida ({regla_id}) → fallback.")
        return {"regla": 0, "params": {}, "razon": "fallback"}

    return {"regla": regla_id, "params": data.get("params", {}), "razon": data.get("razon", "")}


def llamar_llm_heuristico(estado: dict, escenario: str,
                           historial_reciente: list[dict], cfg: dict) -> dict:
    """
    Selector determinista con lógica expandida para las nuevas reglas.
    Umbrales relativos al rango — funciona en [0,1] y [-1,1].
    """
    opinion    = estado["opinion"]
    propaganda = estado["propaganda"]
    confianza  = estado.get("confianza", 0.5)
    neutro     = _neutro(cfg)
    amp        = _amplitud(cfg)
    op_a       = estado.get("opinion_grupo_a", neutro + 0.3 * amp)
    op_b       = estado.get("opinion_grupo_b", neutro - 0.3 * amp)

    tendencia  = [h["opinion"] for h in historial_reciente]
    delta      = tendencia[-1] - tendencia[0] if len(tendencia) > 1 else 0.0

    zona_rechazo = neutro - 0.35 * amp
    umbral_prop  = neutro + 0.15 * amp
    distancia_grupos = abs(op_a - op_b)

    # Narrativa B activa → contagio competitivo
    if "narrativa_b" in estado and abs(estado.get("narrativa_b", 0)) > 0.2:
        return {"regla": 6,
                "params": {"competencia": cfg.get("competencia_peso", 0.4)},
                "razon": "contagio_competitivo: narrativa B activa y relevante"}

    # Grupos muy distantes → HK (solo escucha a similares)
    if distancia_grupos > 0.6 * amp:
        return {"regla": 5,
                "params": {"epsilon": cfg.get("hk_epsilon", 0.3)},
                "razon": f"hk: grupos muy distantes ({distancia_grupos:.2f})"}

    # Rechazo establecido + propaganda → backlash
    if opinion < zona_rechazo and abs(propaganda) > 0.3:
        return {"regla": 3,
                "params": {"penalizacion": 0.12},
                "razon": f"backlash: rechazo establecido (op={opinion:.2f})"}

    # Tendencia fuerte ya iniciada → polarización
    if abs(delta) > 0.05 * amp:
        return {"regla": 4,
                "params": {"fuerza": 0.08},
                "razon": f"polarizacion: tendencia {'positiva' if delta>0 else 'negativa'} fuerte"}

    # Propaganda intensa + baja confianza → umbral
    if abs(propaganda) > abs(umbral_prop) and confianza < 0.5:
        return {"regla": 1,
                "params": {"umbral": round(abs(umbral_prop), 2), "incremento": 0.12},
                "razon": "umbral: propaganda intensa + baja confianza"}

    # Sistema cerca del neutro + grupos similares → homofilia
    if abs(opinion - neutro) < 0.1 * amp and distancia_grupos < 0.4 * amp:
        return {"regla": 8,
                "params": {"tasa": cfg.get("homofilia_tasa", 0.05)},
                "razon": "homofilia: sistema cerca del neutro, grupos convergentes"}

    # Sistema estable → memoria
    if abs(delta) < 0.01 * amp:
        return {"regla": 2,
                "params": {"alpha": 0.75, "beta": 0.18, "gamma": 0.07},
                "razon": "memoria: sistema estable, inercia dominante"}

    return {"regla": 0,
            "params": {"a": 0.72, "b": 0.28},
            "razon": "lineal: condiciones moderadas"}


# ============================================================
# EFECTO DE GRUPOS
# ============================================================

def calcular_efecto_grupos(estado: dict, cfg: dict) -> float:
    """
    Presión social de grupos afín y contrario.
    Opera sobre diferencias → funciona en [0,1] y [-1,1].
    """
    r      = _get_rango(cfg)
    op_a   = estado.get("opinion_grupo_a", r["ejemplo_apoyo"])
    op_b   = estado.get("opinion_grupo_b", r["ejemplo_rechazo"])
    perten = estado.get("pertenencia_grupo", 0.6)
    ref    = perten * op_a + (1.0 - perten) * op_b
    return cfg["efecto_vecinos_peso"] * (ref - estado["opinion"])


# ============================================================
# SIMULADOR PRINCIPAL
# ============================================================

def simular(
    estado_inicial: dict,
    escenario: str = "campana",
    pasos: int = 50,
    cada_n_pasos: int = 5,
    config: dict | None = None,
    verbose: bool = True,
) -> list[dict]:
    """
    Ejecuta la simulación híbrida con todas las reglas disponibles.

    Parámetros
    ----------
    estado_inicial : dict
        Requeridos : opinion, propaganda
        Opcionales : confianza, opinion_grupo_a, opinion_grupo_b,
                     pertenencia_grupo, narrativa_b, sesgo_confirmacion
        Todos los valores de opinión deben estar en el rango configurado.
    escenario      : str — clave en REGLAS
    pasos          : int
    cada_n_pasos   : int — frecuencia de consulta al selector LLM
    config         : dict — sobreescribe DEFAULT_CONFIG
                     Claves clave: "rango", "proveedor", "sesgo_confirmacion"
    verbose        : bool

    Retorna
    -------
    list[dict] — historial de estados (t=0 incluido)
    """
    cfg         = {**DEFAULT_CONFIG, **(config or {})}
    r           = _get_rango(cfg)
    alpha_blend = cfg["alpha_blend"]
    proveedor   = cfg.get("proveedor", "heurístico")

    estado = estado_inicial.copy()
    estado.setdefault("opinion_prev",     estado["opinion"])
    estado.setdefault("confianza",        0.5)
    estado.setdefault("opinion_grupo_a",  min(estado["opinion"] + 0.2 * _amplitud(cfg), r["max"]))
    estado.setdefault("opinion_grupo_b",  max(estado["opinion"] - 0.2 * _amplitud(cfg), r["min"]))
    estado.setdefault("pertenencia_grupo", 0.6)

    historial: list[dict] = [estado.copy()]
    regla_actual   = 0
    params_actuales: dict = {}
    razon_actual   = "inicial"

    def _seleccionar(est, hist):
        ventana = hist[-cfg["ventana_historial_llm"]:]
        dec     = llamar_llm(est, escenario, ventana, cfg)
        r_id    = dec["regla"]
        p       = _validar_params(NOMBRES_REGLAS[r_id], dec.get("params", {}))
        return r_id, p, dec.get("razon", "")

    regla_actual, params_actuales, razon_actual = _seleccionar(estado, historial)
    if verbose:
        log.info(
            f"t=0 | [{proveedor}] rango={r['min']},{r['max']} "
            f"| {NOMBRES_REGLAS[regla_actual]} | {razon_actual}"
        )

    for paso in range(1, pasos + 1):

        if paso % cada_n_pasos == 0:
            regla_actual, params_actuales, razon_actual = _seleccionar(estado, historial)
            if verbose:
                log.info(
                    f"t={paso:3d} | [{proveedor}] {NOMBRES_REGLAS[regla_actual]:22s} "
                    f"op={estado['opinion']:+.3f} | {razon_actual}"
                )

        # Aplicar regla elegida
        regla_func    = REGLAS[escenario].get(regla_actual, regla_lineal)
        estado_regla  = regla_func(estado, params_actuales, cfg)
        opinion_regla = _clip(estado_regla["opinion"], cfg)

        # Tendencia base + blending
        tendencia_base = 0.92 * estado["opinion"] + 0.08 * estado["propaganda"]
        opinion_blend  = alpha_blend * opinion_regla + (1.0 - alpha_blend) * tendencia_base

        # Efecto de grupos + ruido adaptativo
        ruido_std     = cfg["ruido_base"] + cfg["ruido_desconfianza"] * (1.0 - estado["confianza"])
        opinion_final = _clip(
            opinion_blend
            + calcular_efecto_grupos(estado, cfg)
            + np.random.normal(0.0, ruido_std),
            cfg
        )

        # Construir nuevo estado
        nuevo = estado.copy()
        # Si la regla actualizó pertenencia_grupo (homofilia), persiste
        if "pertenencia_grupo" in estado_regla:
            nuevo["pertenencia_grupo"] = estado_regla["pertenencia_grupo"]
        # Métricas auxiliares de reglas avanzadas
        for k in ("_fraccion_adoptantes", "_sim_grupo_a", "_sim_grupo_b"):
            if k in estado_regla:
                nuevo[k] = estado_regla[k]

        nuevo["opinion_prev"]  = estado["opinion"]
        nuevo["opinion"]       = opinion_final
        nuevo["_paso"]         = paso
        nuevo["_regla"]        = regla_actual
        nuevo["_regla_nombre"] = NOMBRES_REGLAS[regla_actual]
        nuevo["_razon"]        = razon_actual
        nuevo["_rango"]        = cfg["rango"]

        estado = nuevo
        historial.append(estado.copy())

    if verbose:
        log.info(
            f"Completo: {pasos} pasos | "
            f"{historial[0]['opinion']:+.3f} → {historial[-1]['opinion']:+.3f} "
            f"(neutro={_neutro(cfg)})"
        )
    return historial


# ============================================================
# SIMULACIÓN MÚLTIPLE
# ============================================================

def simular_multiples(
    estado_inicial: dict,
    escenario: str = "campana",
    pasos: int = 50,
    cada_n_pasos: int = 5,
    config: dict | None = None,
    n_simulaciones: int = 100,
) -> dict:
    """N simulaciones con variación en estado inicial. Retorna distribución."""
    cfg        = {**DEFAULT_CONFIG, **(config or {})}
    r          = _get_rango(cfg)
    ruido_ini  = cfg["ruido_estado_inicial"]
    resultados = np.zeros(n_simulaciones)

    for i in range(n_simulaciones):
        estado_ruido = {
            k: float(np.clip(v + np.random.normal(0, ruido_ini), r["min"], r["max"]))
               if isinstance(v, float) else v
            for k, v in estado_inicial.items()
        }
        hist = simular(estado_ruido, escenario=escenario, pasos=pasos,
                       cada_n_pasos=cada_n_pasos, config=config, verbose=False)
        resultados[i] = hist[-1]["opinion"]

    neutro = _neutro(cfg)
    p10, p25, p50, p75, p90 = np.percentile(resultados, [10, 25, 50, 75, 90])
    return {
        "media":          float(resultados.mean()),
        "std":            float(resultados.std()),
        "p_sobre_neutro": float((resultados > neutro).mean()),
        "percentiles":    {"p10": float(p10), "p25": float(p25), "p50": float(p50),
                           "p75": float(p75), "p90": float(p90)},
        "escenarios":     {"optimista": float(p90), "mediano": float(p50),
                           "pesimista":  float(p10)},
        "neutro":         neutro,
        "n_simulaciones": n_simulaciones,
        "rango":          cfg["rango"],
    }


# ============================================================
# UTILIDADES
# ============================================================

def resumen_historial(historial: list[dict], config: dict | None = None) -> dict:
    """Estadísticas descriptivas. Incluye polarización y regla dominante."""
    cfg       = {**DEFAULT_CONFIG, **(config or {})}
    neutro    = _neutro(cfg)
    opiniones = np.array([h["opinion"] for h in historial])
    reglas    = [h["_regla_nombre"] for h in historial if "_regla_nombre" in h]
    return {
        "opinion_inicial":    float(opiniones[0]),
        "opinion_final":      float(opiniones[-1]),
        "delta_total":        float(opiniones[-1] - opiniones[0]),
        "media":              float(opiniones.mean()),
        "desviacion":         float(opiniones.std()),
        "minimo":             float(opiniones.min()),
        "maximo":             float(opiniones.max()),
        "polarizacion_media": float(np.mean(np.abs(opiniones - neutro))),
        "pasos":              len(historial) - 1,
        "regla_dominante":    Counter(reglas).most_common(1)[0][0] if reglas else "—",
        "neutro":             neutro,
        "rango":              cfg.get("rango", "—"),
    }


# ============================================================
# EJECUCIÓN DIRECTA
# ============================================================
if __name__ == "__main__":
    from scipy.special import erf  # verificar que scipy está disponible

    for nombre_rango in RANGOS_DISPONIBLES:
        r = RANGOS_DISPONIBLES[nombre_rango]
        print(f"\n{'='*65}")
        print(f"Rango: {nombre_rango}")
        print(f"{'='*65}")

        estado = {
            "opinion":          r["defaults"]["opinion_inicial"],
            "propaganda":       r["defaults"]["propaganda"],
            "confianza":        r["defaults"]["confianza"],
            "opinion_grupo_a":  r["defaults"]["opinion_grupo_a"],
            "opinion_grupo_b":  r["defaults"]["opinion_grupo_b"],
            "pertenencia_grupo": 0.65,
            "narrativa_b":      -0.3 if r["min"] < 0 else 0.3,
        }

        config = {
            "rango":              nombre_rango,
            "sesgo_confirmacion": 0.3,
            "hk_epsilon":         0.3,
        }
        hist  = simular(estado, pasos=20, cada_n_pasos=5, config=config, verbose=True)
        stats = resumen_historial(hist, config)

        print(f"\n  opinion: {stats['opinion_inicial']:+.3f} → {stats['opinion_final']:+.3f}")
        print(f"  delta_total:        {stats['delta_total']:+.3f}")
        print(f"  polarizacion_media: {stats['polarizacion_media']:.3f}")
        print(f"  regla_dominante:    {stats['regla_dominante']}")
        print(f"  neutro:             {stats['neutro']}")
