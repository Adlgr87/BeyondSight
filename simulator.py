"""
BeyondSight — Simulador híbrido de dinámica social
Núcleo numérico + LLM como selector de régimen dinámico

Correcciones aplicadas vs versión anterior:
  - subprocess reemplazado por API HTTP de Ollama (robusto en cualquier entorno)
  - clip aplicado inmediatamente al salir de cada regla (evita valores inválidos)
  - efecto_vecinos reemplazado por modelo de dos grupos (captura polarización real)
  - historial reciente incluido en el prompt del LLM (memoria de trayectoria)
  - parámetros externalizados en config dict (sin hardcoding)
  - logging estructurado a archivo + consola
  - manejo explícito de errores con tipos específicos

Autor: BeyondSight Research
"""

import json
import logging
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

import numpy as np
import requests

# ------------------------------------------------------------
# LOGGING — salida a archivo y consola simultáneamente
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
# CONFIGURACIÓN POR DEFECTO — modificar sin tocar el código
# ------------------------------------------------------------
DEFAULT_CONFIG: dict[str, Any] = {
    # LLM
    "ollama_url": "http://localhost:11434/api/generate",
    "ollama_model": "llama3:8b",
    "ollama_timeout": 15,
    "llm_temperature": 0.0,          # 0 = determinista, sin variación espuria
    # Simulación
    "alpha_blend": 0.8,              # peso regla LLM vs tendencia base
    "ruido_base": 0.03,              # ruido mínimo siempre presente
    "ruido_desconfianza": 0.08,      # ruido extra cuando confianza es baja
    "efecto_vecinos_peso": 0.05,     # cuánto arrastran los vecinos
    "ventana_historial_llm": 6,      # pasos recientes que ve el LLM
}


# ------------------------------------------------------------
# REGLAS DE TRANSICIÓN
# Cada regla recibe (estado, params) y devuelve nuevo estado.
# Todas garantizan opinion ∈ [0, 1] al salir.
# ------------------------------------------------------------

def regla_lineal(estado: dict, params: dict) -> dict:
    """Cambio proporcional a opinión actual y propaganda."""
    a = params.get("a", 0.7)
    b = params.get("b", 0.3)
    val = a * estado["opinion"] + b * estado["propaganda"]
    nuevo = {**estado}
    nuevo["opinion"] = float(np.clip(val, 0.0, 1.0))
    return nuevo


def regla_umbral(estado: dict, params: dict) -> dict:
    """Salto no lineal cuando la propaganda supera un umbral crítico."""
    umbral = params.get("umbral", 0.65)
    incremento = params.get("incremento", 0.15)
    if estado["propaganda"] > umbral:
        val = estado["opinion"] + incremento * (1.0 - estado["opinion"])
    else:
        val = estado["opinion"]
    nuevo = {**estado}
    nuevo["opinion"] = float(np.clip(val, 0.0, 1.0))
    return nuevo


def regla_memoria(estado: dict, params: dict) -> dict:
    """El estado presente depende también del estado anterior (inercia)."""
    alpha = params.get("alpha", 0.7)
    beta  = params.get("beta",  0.2)
    gamma = params.get("gamma", 0.1)
    prev  = estado.get("opinion_prev", estado["opinion"])
    val   = alpha * estado["opinion"] + beta * prev + gamma * estado["propaganda"]
    nuevo = {**estado}
    nuevo["opinion"] = float(np.clip(val, 0.0, 1.0))
    return nuevo


def regla_backlash(estado: dict, params: dict) -> dict:
    """Reacción negativa cuando la opinión ya es baja: la propaganda genera rechazo."""
    umbral_inf  = params.get("umbral_inferior", 0.35)
    penalizacion = params.get("penalizacion", 0.15)
    if estado["opinion"] < umbral_inf:
        val = estado["opinion"] - penalizacion * estado["propaganda"]
    else:
        val = estado["opinion"]
    nuevo = {**estado}
    # CORRECCIÓN: clip aquí — antes podía producir valores negativos sin control
    nuevo["opinion"] = float(np.clip(val, 0.0, 1.0))
    return nuevo


def regla_polarizacion(estado: dict, params: dict) -> dict:
    """
    Refuerza la posición actual: opiniones altas suben, bajas bajan.
    Captura el efecto 'cámara de eco'.
    """
    fuerza = params.get("fuerza", 0.1)
    opinion = estado["opinion"]
    if opinion >= 0.5:
        val = opinion + fuerza * (1.0 - opinion)
    else:
        val = opinion - fuerza * opinion
    nuevo = {**estado}
    nuevo["opinion"] = float(np.clip(val, 0.0, 1.0))
    return nuevo


# Registro de reglas disponibles por escenario
REGLAS: dict[str, dict[int, Any]] = {
    "campana": {
        0: regla_lineal,
        1: regla_umbral,
        2: regla_memoria,
        3: regla_backlash,
        4: regla_polarizacion,
    }
}

NOMBRES_REGLAS = {
    0: "lineal",
    1: "umbral",
    2: "memoria",
    3: "backlash",
    4: "polarizacion",
}


# ------------------------------------------------------------
# CAPA LLM
# ------------------------------------------------------------

def _construir_prompt(estado: dict, escenario: str, historial_reciente: list[dict]) -> str:
    """
    Construye el prompt incluyendo tendencia reciente.
    CORRECCIÓN: el LLM ahora ve los últimos N pasos, no solo el estado actual.
    """
    tendencia = [round(h["opinion"], 3) for h in historial_reciente]
    delta = round(tendencia[-1] - tendencia[0], 3) if len(tendencia) > 1 else 0.0
    direccion = "subiendo" if delta > 0.02 else ("bajando" if delta < -0.02 else "estable")

    return f"""Eres un selector de reglas para simulación de dinámica social.
Escenario: {escenario}

Estado actual:
{json.dumps({k: round(v, 3) if isinstance(v, float) else v for k, v in estado.items()}, ensure_ascii=False)}

Tendencia reciente de opinión (últimos {len(tendencia)} pasos): {tendencia}
Dirección: {direccion} (Δ={delta:+.3f})

Reglas disponibles:
0: lineal      — cambio proporcional suave
1: umbral      — salto brusco si propaganda > umbral crítico
2: memoria     — inercia del estado pasado modera el cambio
3: backlash    — propaganda genera rechazo cuando opinión ya es baja
4: polarizacion — refuerza la posición actual (efecto cámara de eco)

Instrucciones:
- Elige la regla más adecuada dado el estado Y la tendencia reciente.
- Asigna parámetros realistas dentro de estos rangos:
  lineal: a ∈ [0.5,0.9], b ∈ [0.1,0.5]
  umbral: umbral ∈ [0.4,0.8], incremento ∈ [0.05,0.25]
  memoria: alpha ∈ [0.5,0.8], beta ∈ [0.1,0.3], gamma ∈ [0.05,0.2]
  backlash: umbral_inferior ∈ [0.2,0.5], penalizacion ∈ [0.05,0.25]
  polarizacion: fuerza ∈ [0.05,0.2]

Responde SOLO con JSON válido, sin texto adicional:
{{"regla": <0-4>, "params": {{...}}, "razon": "<explicacion breve>"}}
Si no puedes decidir, usa: {{"regla": 0, "params": {{}}, "razon": "fallback"}}
"""


def llamar_llm(
    estado: dict,
    escenario: str,
    historial_reciente: list[dict],
    config: dict,
) -> dict:
    """
    Llama al LLM vía API HTTP de Ollama.
    CORRECCIÓN: usa requests en vez de subprocess — funciona en cualquier entorno.
    Retorna siempre un dict válido aunque falle.
    """
    prompt = _construir_prompt(estado, escenario, historial_reciente)
    fallback = {"regla": 0, "params": {}, "razon": "fallback"}

    try:
        resp = requests.post(
            config["ollama_url"],
            json={
                "model": config["ollama_model"],
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": config["llm_temperature"]},
            },
            timeout=config["ollama_timeout"],
        )
        resp.raise_for_status()
        texto = resp.json().get("response", "")

        # Extraer JSON del texto (el LLM puede añadir texto antes/después)
        inicio = texto.find("{")
        fin = texto.rfind("}") + 1
        if inicio == -1 or fin == 0:
            log.warning("LLM no devolvió JSON parseable. Usando fallback.")
            return fallback

        data = json.loads(texto[inicio:fin])

        # Validar estructura mínima
        regla_id = int(data.get("regla", 0))
        if regla_id not in REGLAS.get(escenario, {}):
            log.warning(f"LLM eligió regla inválida ({regla_id}). Usando fallback.")
            return fallback

        return {
            "regla": regla_id,
            "params": data.get("params", {}),
            "razon": data.get("razon", ""),
        }

    except requests.exceptions.ConnectionError:
        log.error("Ollama no responde. ¿Está corriendo? (ollama serve)")
        return fallback
    except requests.exceptions.Timeout:
        log.warning(f"Timeout ({config['ollama_timeout']}s) llamando al LLM.")
        return fallback
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        log.warning(f"Error parseando respuesta LLM: {exc}")
        return fallback


def llamar_llm_heuristico(estado: dict, escenario: str, historial_reciente: list[dict]) -> dict:
    """
    Fallback determinista para pruebas sin Ollama.
    Reglas basadas en lógica explícita, no en LLM.
    """
    opinion = estado["opinion"]
    propaganda = estado["propaganda"]
    confianza = estado.get("confianza", 0.5)

    tendencia = [h["opinion"] for h in historial_reciente]
    delta = tendencia[-1] - tendencia[0] if len(tendencia) > 1 else 0.0

    # Lógica de selección explícita y documentada
    if opinion < 0.35 and propaganda > 0.5:
        return {"regla": 3, "params": {"umbral_inferior": 0.35, "penalizacion": 0.12}, "razon": "backlash: opinión baja + propaganda alta"}

    if abs(delta) > 0.05 and opinion > 0.55:
        return {"regla": 4, "params": {"fuerza": 0.08}, "razon": "polarización: tendencia fuerte ya iniciada"}

    if propaganda > 0.65 and confianza < 0.5:
        return {"regla": 1, "params": {"umbral": 0.65, "incremento": 0.12}, "razon": "umbral: propaganda alta + desconfianza"}

    if abs(delta) < 0.01:
        return {"regla": 2, "params": {"alpha": 0.75, "beta": 0.18, "gamma": 0.07}, "razon": "memoria: sistema estable, inercia dominante"}

    return {"regla": 0, "params": {"a": 0.72, "b": 0.28}, "razon": "lineal: condiciones moderadas"}


# ------------------------------------------------------------
# MODELO DE DOS GRUPOS (reemplaza efecto_vecinos naive)
# CORRECCIÓN: antes usaba (0.5 - opinion) como proxy de vecinos,
# lo que destruía polarización. Ahora modela dos grupos reales.
# ------------------------------------------------------------

def calcular_efecto_grupos(estado: dict, config: dict) -> float:
    """
    Modela la presión social de dos grupos con opiniones distintas.
    El agente es atraído hacia su grupo de pertenencia.

    Variables del estado usadas:
      opinion_grupo_a    — opinión media del grupo afín (default 0.7)
      opinion_grupo_b    — opinión media del grupo contrario (default 0.3)
      pertenencia_grupo  — qué tan fuerte es la identidad grupal [0,1] (default 0.6)
    """
    op_a   = estado.get("opinion_grupo_a", 0.7)
    op_b   = estado.get("opinion_grupo_b", 0.3)
    perten = estado.get("pertenencia_grupo", 0.6)
    opinion_actual = estado["opinion"]

    # Opinión de referencia del entorno social ponderada por pertenencia
    referencia_social = perten * op_a + (1.0 - perten) * op_b

    # Presión hacia la referencia
    return config["efecto_vecinos_peso"] * (referencia_social - opinion_actual)


# ------------------------------------------------------------
# SIMULADOR PRINCIPAL
# ------------------------------------------------------------

def simular(
    estado_inicial: dict,
    escenario: str = "campana",
    pasos: int = 50,
    cada_n_pasos: int = 5,
    usar_llm_real: bool = False,
    config: dict | None = None,
    verbose: bool = True,
) -> list[dict]:
    """
    Ejecuta la simulación híbrida y retorna el historial completo.

    Parámetros
    ----------
    estado_inicial : dict con claves:
        opinion, opinion_prev, propaganda, confianza, tension,
        opinion_grupo_a, opinion_grupo_b, pertenencia_grupo
    escenario : str — clave en REGLAS
    pasos : int — número de pasos temporales
    cada_n_pasos : int — cada cuántos pasos consulta al LLM
    usar_llm_real : bool — True = Ollama, False = heurístico
    config : dict — sobreescribe DEFAULT_CONFIG parcialmente
    verbose : bool — imprime/loggea progreso

    Retorna
    -------
    list[dict] — historial de estados incluyendo t=0
    """
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    alpha_blend = cfg["alpha_blend"]

    estado = deepcopy(estado_inicial)
    # Garantizar claves opcionales con defaults
    estado.setdefault("opinion_prev", estado["opinion"])
    estado.setdefault("confianza", 0.5)
    estado.setdefault("tension", 0.3)
    estado.setdefault("opinion_grupo_a", min(estado["opinion"] + 0.2, 1.0))
    estado.setdefault("opinion_grupo_b", max(estado["opinion"] - 0.2, 0.0))
    estado.setdefault("pertenencia_grupo", 0.6)

    historial: list[dict] = [{**estado}]
    regla_actual = 0
    params_actuales: dict = {}
    razon_actual = "inicial"

    def _seleccionar_regla(est: dict, hist: list[dict]) -> tuple[int, dict, str]:
        ventana = hist[-cfg["ventana_historial_llm"]:]
        if usar_llm_real:
            dec = llamar_llm(est, escenario, ventana, cfg)
        else:
            dec = llamar_llm_heuristico(est, escenario, ventana)
        return dec["regla"], dec.get("params", {}), dec.get("razon", "")

    # Selección inicial
    regla_actual, params_actuales, razon_actual = _seleccionar_regla(estado, historial)
    if verbose:
        log.info(f"t=0 | Regla inicial: {NOMBRES_REGLAS[regla_actual]} | {razon_actual}")

    for paso in range(1, pasos + 1):

        # --- 1. Consultar LLM cada N pasos ---
        if paso % cada_n_pasos == 0:
            regla_actual, params_actuales, razon_actual = _seleccionar_regla(estado, historial)
            if verbose:
                log.info(
                    f"t={paso:3d} | Regla: {NOMBRES_REGLAS[regla_actual]:14s} "
                    f"| opinion={estado['opinion']:.3f} | {razon_actual}"
                )

        # --- 2. Aplicar regla elegida ---
        regla_func = REGLAS[escenario].get(regla_actual, regla_lineal)
        estado_regla = regla_func(estado, params_actuales)
        # clip ya aplicado dentro de cada regla, pero doble seguridad:
        opinion_regla = float(np.clip(estado_regla["opinion"], 0.0, 1.0))

        # --- 3. Tendencia base (amortiguador ante alucinaciones) ---
        tendencia_base = 0.92 * estado["opinion"] + 0.08 * estado["propaganda"]

        # --- 4. Blending ---
        opinion_blend = alpha_blend * opinion_regla + (1.0 - alpha_blend) * tendencia_base

        # --- 5. Efecto de grupos (modelo dos grupos, no naive 0.5) ---
        efecto_grupos = calcular_efecto_grupos(estado, cfg)
        opinion_con_grupos = opinion_blend + efecto_grupos

        # --- 6. Ruido adaptativo según confianza ---
        ruido_std = cfg["ruido_base"] + cfg["ruido_desconfianza"] * (1.0 - estado["confianza"])
        ruido = float(np.random.normal(0.0, ruido_std))
        opinion_final = float(np.clip(opinion_con_grupos + ruido, 0.0, 1.0))

        # --- 7. Construir nuevo estado ---
        estado = {
            **estado,
            "opinion_prev": estado["opinion"],
            "opinion": opinion_final,
            "_paso": paso,
            "_regla": regla_actual,
            "_regla_nombre": NOMBRES_REGLAS[regla_actual],
            "_razon": razon_actual,
        }
        historial.append({**estado})

    if verbose:
        log.info(
            f"Simulación completa: {pasos} pasos | "
            f"opinión inicial={historial[0]['opinion']:.3f} → final={historial[-1]['opinion']:.3f}"
        )

    return historial


# ------------------------------------------------------------
# UTILIDADES DE ANÁLISIS
# ------------------------------------------------------------

def resumen_historial(historial: list[dict]) -> dict:
    """Estadísticas descriptivas de la trayectoria."""
    opiniones = np.array([h["opinion"] for h in historial])
    return {
        "opinion_inicial": float(opiniones[0]),
        "opinion_final": float(opiniones[-1]),
        "delta_total": float(opiniones[-1] - opiniones[0]),
        "media": float(opiniones.mean()),
        "desviacion": float(opiniones.std()),
        "minimo": float(opiniones.min()),
        "maximo": float(opiniones.max()),
        "pasos": len(historial) - 1,
    }


# ------------------------------------------------------------
# EJECUCIÓN DIRECTA (sin Streamlit)
# ------------------------------------------------------------

if __name__ == "__main__":
    estado_inicial = {
        "opinion": 0.5,
        "propaganda": 0.7,
        "confianza": 0.4,
        "tension": 0.3,
        "opinion_grupo_a": 0.72,
        "opinion_grupo_b": 0.28,
        "pertenencia_grupo": 0.65,
    }

    print("\n" + "="*60)
    print("BeyondSight — Simulación heurística (sin Ollama)")
    print("="*60 + "\n")

    historial = simular(
        estado_inicial,
        escenario="campana",
        pasos=30,
        cada_n_pasos=5,
        usar_llm_real=False,
        verbose=True,
    )

    stats = resumen_historial(historial)
    print("\n--- Resumen ---")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print("\n--- Trayectoria (cada 5 pasos) ---")
    for h in historial[::5]:
        paso = h.get("_paso", 0)
        regla = h.get("_regla_nombre", "inicial")
        print(f"  t={paso:3d} | opinion={h['opinion']:.4f} | regla={regla}")
