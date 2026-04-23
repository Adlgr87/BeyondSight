"""
BeyondSight — Discrete Engine (Subordinado a SocialArchitect)
Motor de simulación discreta de reglas con compatibilidad backward.
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import networkx as nx
import numpy as np
from scipy.special import erf


logger = logging.getLogger(__name__)

DEFAULT_PAYOFF_MATRIX: Dict[str, Dict[str, float]] = {
    "A": {"A": 1.0, "B": 0.35, "C": 0.45},
    "B": {"A": 0.35, "B": 1.0, "C": 0.40},
    "C": {"A": 0.45, "B": 0.40, "C": 1.0},
}

RANGOS_DISPONIBLES: Dict[str, Tuple[float, float]] = {
    "opinion": (0.0, 1.0),
    "propaganda": (0.0, 1.0),
    "confianza": (0.0, 1.0),
    "tension": (0.0, 1.0),
    "pertenencia_grupo": (0.0, 1.0),
}

_ESCENARIOS_VALIDOS = {"campana"}

_RULE_DEFAULTS: Dict[str, Any] = {
    "ruido": 0.02,
    "inercia": 0.72,
    "peso_interaccion": 0.15,
    "efecto_vecinos_peso": 0.08,
    "polarizacion_umbral": 0.25,
    "alpha_hk": 0.30,
    "beta_contagio": 0.12,
    "media_umbral": 0.5,
    "desviacion_umbral": 0.15,
    "suavidad_umbral": 6.0,
}


def _clip01(value: float) -> float:
    return float(max(0.0, min(1.0, value)))


def _validate_groups(grupos: Dict[str, float]) -> Dict[str, float]:
    required = {"A", "B", "C"}
    missing = required - set(grupos.keys())
    if missing:
        raise ValueError(f"Faltan grupos requeridos: {sorted(missing)}")
    normalized = {k: _clip01(float(v)) for k, v in grupos.items()}
    return normalized


def _coerce_legacy_state_to_groups(estado: Dict[str, Any]) -> Dict[str, float]:
    a = float(estado.get("opinion_grupo_a", estado.get("A", estado.get("opinion", 0.5))))
    b = float(estado.get("opinion_grupo_b", estado.get("B", estado.get("opinion", 0.5))))
    c = float(estado.get("opinion_grupo_c", estado.get("C", estado.get("opinion", 0.5))))
    return _validate_groups({"A": a, "B": b, "C": c})


def _group_scalar(grupos: Dict[str, float]) -> float:
    return float(np.mean([grupos["A"], grupos["B"], grupos["C"]]))


def calcular_efecto_grupos(estado: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> float:
    """
    Empuja la opinión individual hacia una referencia social ponderada por pertenencia.
    Compatibilidad con tests legacy.
    """
    cfg = cfg or {}
    peso = float(cfg.get("efecto_vecinos_peso", _RULE_DEFAULTS["efecto_vecinos_peso"]))
    opinion = _clip01(float(estado.get("opinion", 0.5)))
    opinion_a = _clip01(float(estado.get("opinion_grupo_a", 0.5)))
    opinion_b = _clip01(float(estado.get("opinion_grupo_b", 0.5)))
    pertenencia = _clip01(float(estado.get("pertenencia_grupo", 0.5)))

    referencia = pertenencia * opinion_a + (1.0 - pertenencia) * opinion_b
    return float((referencia - opinion) * max(0.0, peso))


def regla_hk(opinion: float, vecinos: Iterable[float], alpha_hk: float = _RULE_DEFAULTS["alpha_hk"]) -> float:
    """
    Regla de Hegselmann-Krause simplificada (confidence bound).
    `alpha_hk` evita confusión con alpha_blend del motor principal.
    """
    opinion = _clip01(opinion)
    vecinos = [float(v) for v in vecinos]
    if not vecinos:
        return opinion
    umbral = max(0.01, min(1.0, float(alpha_hk)))
    compatibles = [v for v in vecinos if abs(v - opinion) <= umbral]
    if not compatibles:
        return opinion
    return _clip01(float(np.mean(compatibles)))


def regla_contagio_competitivo(opinion: float, propaganda: float, beta_contagio: float = _RULE_DEFAULTS["beta_contagio"]) -> float:
    opinion = _clip01(opinion)
    propaganda = _clip01(propaganda)
    beta = max(0.0, min(1.0, float(beta_contagio)))
    return _clip01(opinion + beta * (propaganda - opinion))


def regla_umbral_heterogeneo(
    opinion: float,
    señal: float,
    media_umbral: float = _RULE_DEFAULTS["media_umbral"],
    desviacion_umbral: float = _RULE_DEFAULTS["desviacion_umbral"],
    suavidad_umbral: float = _RULE_DEFAULTS["suavidad_umbral"],
) -> float:
    """
    Adopción suave por umbral heterogéneo usando erf (importado a nivel de módulo).
    """
    opinion = _clip01(opinion)
    señal = _clip01(señal)
    media = _clip01(media_umbral)
    desv = max(1e-6, float(desviacion_umbral))
    suavidad = max(1e-6, float(suavidad_umbral))

    z = (señal - media) / (desv * np.sqrt(2.0))
    prob_adopcion = 0.5 * (1.0 + erf(z))
    ajuste = (prob_adopcion - opinion) / suavidad
    return _clip01(opinion + ajuste)


def _network_for(red: str, n: int, seed: int) -> nx.Graph:
    if red == "small_world":
        return nx.watts_strogatz_graph(max(8, n), k=4, p=0.2, seed=seed)
    if red == "scale_free":
        return nx.barabasi_albert_graph(max(8, n), m=2, seed=seed)
    if red == "random":
        return nx.erdos_renyi_graph(max(8, n), p=0.25, seed=seed)
    return nx.watts_strogatz_graph(max(8, n), k=4, p=0.2, seed=seed)


def get_graph_metrics(network_type: str) -> Dict[str, float]:
    grafo = _network_for(network_type, n=30, seed=42)
    if grafo.number_of_nodes() == 0:
        return {"density": 0.0, "clustering": 0.0, "avg_degree": 0.0}
    density = float(nx.density(grafo))
    clustering = float(nx.average_clustering(grafo))
    avg_degree = float(np.mean([d for _, d in grafo.degree()])) if grafo.number_of_nodes() else 0.0
    return {
        "density": density,
        "clustering": clustering,
        "avg_degree": avg_degree,
    }


def _apply_step(
    opinion: float,
    grupos: Dict[str, float],
    alpha_blend: float,
    cfg: Dict[str, Any],
    rng: np.random.Generator,
) -> float:
    inercia = max(0.0, min(1.0, float(cfg.get("inercia", _RULE_DEFAULTS["inercia"]))))
    ruido = max(0.0, float(cfg.get("ruido", _RULE_DEFAULTS["ruido"])))
    peso_interaccion = max(0.0, min(1.0, float(cfg.get("peso_interaccion", _RULE_DEFAULTS["peso_interaccion"]))))
    propaganda = _clip01(float(np.mean(list(grupos.values()))))

    opinion_hk = regla_hk(opinion, vecinos=grupos.values(), alpha_hk=float(cfg.get("alpha_hk", _RULE_DEFAULTS["alpha_hk"])))
    opinion_contagio = regla_contagio_competitivo(opinion_hk, propaganda, beta_contagio=float(cfg.get("beta_contagio", _RULE_DEFAULTS["beta_contagio"])))
    opinion_umbral = regla_umbral_heterogeneo(
        opinion_contagio,
        señal=propaganda,
        media_umbral=float(cfg.get("media_umbral", _RULE_DEFAULTS["media_umbral"])),
        desviacion_umbral=float(cfg.get("desviacion_umbral", _RULE_DEFAULTS["desviacion_umbral"])),
        suavidad_umbral=float(cfg.get("suavidad_umbral", _RULE_DEFAULTS["suavidad_umbral"])),
    )

    blend = _clip01(float(alpha_blend))
    social_pull = _group_scalar(grupos)
    next_op = inercia * opinion + (1.0 - inercia) * ((1.0 - blend) * opinion_umbral + blend * social_pull)
    next_op += peso_interaccion * (social_pull - opinion)
    next_op += float(rng.normal(0.0, ruido))
    return _clip01(next_op)


def resumen_historial(historial: List[Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Resumen robusto para historial legacy (lista de dicts) y moderno (lista de floats).
    """
    if not historial:
        return {
            "pasos": 0,
            "opinion_inicial": 0.0,
            "opinion_final": 0.0,
            "minimo": 0.0,
            "maximo": 0.0,
            "delta_total": 0.0,
            "polarizacion_media": 0.0,
            "estabilidad": 1.0,
            "convergencia": 1.0,
            "volatilidad": 0.0,
        }

    if isinstance(historial[0], dict):
        serie = [float(h.get("opinion", 0.0)) for h in historial]
        pasos = max(0, len(historial) - 1)
    else:
        serie = [float(x) for x in historial]
        pasos = max(0, len(serie) - 1)

    arr = np.array(serie, dtype=float)
    diffs = np.diff(arr) if len(arr) > 1 else np.array([0.0])

    opinion_inicial = _clip01(float(arr[0]))
    opinion_final = _clip01(float(arr[-1]))
    minimo = _clip01(float(np.min(arr)))
    maximo = _clip01(float(np.max(arr)))
    delta_total = float(opinion_final - opinion_inicial)
    polarizacion_media = float(np.mean(np.abs(arr - 0.5)) * 2.0)
    volatilidad = float(np.mean(np.abs(diffs)))
    convergencia = float(1.0 - min(1.0, np.mean(np.abs(diffs[-min(10, len(diffs)):])) * 10.0))
    estabilidad = float(1.0 - min(1.0, float(np.std(arr)) * 2.0))

    return {
        "pasos": int(pasos),
        "opinion_inicial": opinion_inicial,
        "opinion_final": opinion_final,
        "minimo": minimo,
        "maximo": maximo,
        "delta_total": delta_total,
        "polarizacion_media": max(0.0, min(1.0, polarizacion_media)),
        "estabilidad": max(0.0, min(1.0, estabilidad)),
        "convergencia": max(0.0, min(1.0, convergencia)),
        "volatilidad": max(0.0, volatilidad),
    }


def _simular_legacy(
    estado_inicial: Dict[str, Any],
    escenario: str = "campana",
    pasos: int = 20,
    cada_n_pasos: int = 5,
    config: Optional[Dict[str, Any]] = None,
    verbose: bool = False,
) -> List[Dict[str, Any]]:
    cfg = dict(_RULE_DEFAULTS)
    cfg.update(config or {})

    if escenario not in _ESCENARIOS_VALIDOS:
        logger.warning("Escenario '%s' no soportado. Fallback a 'campana'.", escenario)
        escenario = "campana"

    seed = int(cfg.get("seed", 42))
    rng = np.random.default_rng(seed)

    opinion = _clip01(float(estado_inicial.get("opinion", 0.5)))
    historial: List[Dict[str, Any]] = []
    inicial = dict(estado_inicial)
    inicial["_paso"] = 0
    inicial["_regla_nombre"] = "estado_inicial"
    inicial["opinion"] = opinion
    historial.append(inicial)

    grupos = _coerce_legacy_state_to_groups(estado_inicial)
    alpha_blend = _clip01(float(cfg.get("alpha", 0.5)))

    for paso in range(1, int(pasos) + 1):
        opinion = _apply_step(opinion, grupos=grupos, alpha_blend=alpha_blend, cfg=cfg, rng=rng)
        estado = dict(estado_inicial)
        estado["_paso"] = paso
        estado["_regla_nombre"] = "campana_compuesta"
        estado["opinion"] = opinion
        estado["opinion_grupo_a"] = grupos["A"]
        estado["opinion_grupo_b"] = grupos["B"]
        estado["opinion_grupo_c"] = grupos["C"]
        historial.append(estado)

        if verbose and cada_n_pasos > 0 and (paso % int(cada_n_pasos) == 0):
            logger.info("Paso %s/%s opinion=%.4f", paso, pasos, opinion)

    return historial


def _simular_moderno(
    *,
    alpha: float,
    grupos: Dict[str, float],
    timesteps: int,
    red: str = "small_world",
    escenario: str = "campana",
    seed: int = 42,
    llm: Optional[Dict[str, Any]] = None,
    payoff_matrix: Optional[Dict[str, Dict[str, float]]] = None,
) -> List[float]:
    cfg = dict(_RULE_DEFAULTS)
    if llm:
        cfg.update({k: v for k, v in llm.items() if isinstance(v, (int, float, str, bool))})

    if escenario not in _ESCENARIOS_VALIDOS:
        logger.warning("Escenario '%s' no soportado. Fallback a 'campana'.", escenario)
        escenario = "campana"

    grupos_val = _validate_groups(grupos)
    alpha_blend = _clip01(float(alpha))
    timesteps = max(1, int(timesteps))

    rng = np.random.default_rng(int(seed))
    _ = _network_for(red, n=30, seed=int(seed))
    _payoff = payoff_matrix or DEFAULT_PAYOFF_MATRIX
    opinion = _group_scalar(grupos_val)

    historial: List[float] = [opinion]
    for _step in range(timesteps):
        opinion = _apply_step(opinion, grupos=grupos_val, alpha_blend=alpha_blend, cfg=cfg, rng=rng)
        historial.append(opinion)
    return historial


def simular(*args: Any, **kwargs: Any) -> List[Any]:
    """
    Función compatible con dos APIs:
    - Legacy tests: simular(estado_inicial: dict, escenario=..., pasos=..., config=...)
    - Nueva arquitectura: simular(alpha=..., grupos=..., timesteps=..., red=..., escenario=..., ...)
    """
    if args and isinstance(args[0], dict):
        estado = args[0]
        return _simular_legacy(
            estado_inicial=estado,
            escenario=kwargs.get("escenario", "campana"),
            pasos=int(kwargs.get("pasos", 20)),
            cada_n_pasos=int(kwargs.get("cada_n_pasos", 5)),
            config=kwargs.get("config"),
            verbose=bool(kwargs.get("verbose", False)),
        )

    required = ("alpha", "grupos", "timesteps")
    missing = [k for k in required if k not in kwargs]
    if missing:
        raise ValueError(f"Faltan parámetros requeridos para simular API moderna: {missing}")

    return _simular_moderno(
        alpha=float(kwargs["alpha"]),
        grupos=dict(kwargs["grupos"]),
        timesteps=int(kwargs["timesteps"]),
        red=str(kwargs.get("red", "small_world")),
        escenario=str(kwargs.get("escenario", "campana")),
        seed=int(kwargs.get("seed", 42)),
        llm=kwargs.get("llm"),
        payoff_matrix=kwargs.get("payoff_matrix"),
    )


def simular_multiples(
    *,
    n: int,
    alpha: float,
    grupos: Dict[str, float],
    timesteps: int,
    red: str = "small_world",
    escenario: str = "campana",
    llm: Optional[Dict[str, Any]] = None,
    payoff_matrix: Optional[Dict[str, Dict[str, float]]] = None,
) -> Tuple[List[List[float]], Dict[str, Any]]:
    runs = max(1, int(n))
    series: List[List[float]] = []
    for i in range(runs):
        hist = _simular_moderno(
            alpha=alpha,
            grupos=grupos,
            timesteps=timesteps,
            red=red,
            escenario=escenario,
            seed=42 + i,
            llm=llm,
            payoff_matrix=payoff_matrix,
        )
        series.append(hist)

    finals = np.array([h[-1] for h in series], dtype=float)
    aggregate = {
        "runs": runs,
        "mean_final_opinion": float(np.mean(finals)),
        "std_final_opinion": float(np.std(finals)),
    }
    base_stats = resumen_historial([float(np.mean([s[t] for s in series])) for t in range(len(series[0]))], config={})
    aggregate.update(base_stats)
    return series, aggregate


def llamar_llm(prompt: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Stub operativo seguro para compatibilidad de tests de integración:
    devuelve configuración saneada determinística cuando no hay proveedor externo.
    """
    cfg = config or {}
    modelo = str(cfg.get("modelo", "fallback"))
    proveedor = str(cfg.get("proveedor", "heuristico"))
    return {
        "proveedor": proveedor,
        "modelo": modelo,
        "prompt_hash": abs(hash(json.dumps(prompt, sort_keys=True))) % 10_000_000,
        "status": "ok",
    }


def iter_simulation_ticks(
    *,
    alpha: float,
    grupos: Dict[str, float],
    timesteps: int,
    red: str = "small_world",
    escenario: str = "campana",
    seed: int = 42,
) -> Iterable[Dict[str, Any]]:
    historial = _simular_moderno(
        alpha=alpha,
        grupos=grupos,
        timesteps=timesteps,
        red=red,
        escenario=escenario,
        seed=seed,
    )
    for idx, value in enumerate(historial):
        yield {"tick": idx, "opinion": float(value), "escenario": escenario, "red": red}


def save_historial_json(historial: List[Any], path: str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)
