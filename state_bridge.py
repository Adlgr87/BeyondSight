"""
BeyondSight — State Bridge (FASE 2.1)
======================================
Adapts the raw simulator state dict into a typed VisualizationState object.
The UI (app.py) should consume VisualizationState exclusively — never the raw dict.

This decouples the visualisation layer from the simulator internals,
making it safe to refactor either side independently.

Referencia: Adapter pattern (GoF), Type Dispatching with isinstance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ============================================================
# TYPED VISUALIZATION STATE
# ============================================================

@dataclass
class VisualizationState:
    """
    Typed, UI-safe representation of a single simulation tick.

    All fields that are model-specific are Optional — callers must
    check for None before rendering.

    Attributes:
        paso:               Time step index (0 = initial state).
        opinion:            Current opinion value (clipped to valid range).
        opinion_prev:       Opinion at previous tick (for delta calculation).
        regla_nombre:       Name of the transition rule active at this tick.
        razon:              Explanation string from the rule selector.
        rango:              Human-readable range label (e.g. "[0, 1] — Probabilístico").
        es_fallback:        True when the LLM was unavailable and the heuristic was used.
        opinion_changed:    True when opinion moved more than the change threshold.

        -- Model-specific optional fields --
        fraccion_adoptantes: Granovetter cascade adoption fraction [0, 1].
        sim_grupo_a:         Homophily similarity to group A [0, 1].
        sim_grupo_b:         Homophily similarity to group B [0, 1].
        pertenencia_grupo:   Current group identity intensity [0.1, 0.9].
        llm_regla_id:        Integer rule ID (0–8).
    """

    paso:              int
    opinion:           float
    opinion_prev:      float
    regla_nombre:      str
    razon:             str
    rango:             str
    es_fallback:       bool = False
    opinion_changed:   bool = False

    # Optional model-specific metrics
    fraccion_adoptantes: float | None = None
    sim_grupo_a:         float | None = None
    sim_grupo_b:         float | None = None
    pertenencia_grupo:   float | None = None
    llm_regla_id:        int   | None = None

    # Extra passthrough for any future fields not yet in the schema
    _extra: dict = field(default_factory=dict, repr=False)

    @property
    def delta(self) -> float:
        """Opinion change from previous tick."""
        return self.opinion - self.opinion_prev

    @property
    def es_umbral_heterogeneo(self) -> bool:
        return self.regla_nombre == "umbral_heterogeneo"

    @property
    def es_homofilia(self) -> bool:
        return self.regla_nombre == "homofilia"


# ============================================================
# CONVERSION FUNCTION
# ============================================================

def estado_a_vis(estado: dict, modelo_activo: str | None = None) -> VisualizationState:
    """
    Converts a raw simulator state dict into a VisualizationState.

    Type dispatching is used to populate model-specific optional fields
    based on the active model name — safe regardless of which keys are
    present in the dict.

    Args:
        estado:         Raw state dict from simular() or iter_simulation_ticks().
        modelo_activo:  Override for the active model name (uses _regla_nombre if None).

    Returns:
        A fully populated VisualizationState.
    """
    regla_nombre = estado.get("_regla_nombre", modelo_activo or "?")

    base = VisualizationState(
        paso          = int(estado.get("_paso", 0)),
        opinion       = float(estado.get("opinion", 0.0)),
        opinion_prev  = float(estado.get("opinion_prev", estado.get("opinion", 0.0))),
        regla_nombre  = regla_nombre,
        razon         = str(estado.get("_razon", "")),
        rango         = str(estado.get("_rango", "[0, 1] — Probabilístico")),
        es_fallback   = bool(estado.get("_llm_fallback", False)),
        opinion_changed = bool(estado.get("_opinion_changed", False)),
        llm_regla_id  = int(estado["_regla"]) if "_regla" in estado else None,
    )

    # Model-specific dispatching — only populate when the key is present
    if "_fraccion_adoptantes" in estado:
        base.fraccion_adoptantes = float(estado["_fraccion_adoptantes"])

    if "_sim_grupo_a" in estado:
        base.sim_grupo_a = float(estado["_sim_grupo_a"])

    if "_sim_grupo_b" in estado:
        base.sim_grupo_b = float(estado["_sim_grupo_b"])

    if "pertenencia_grupo" in estado:
        base.pertenencia_grupo = float(estado["pertenencia_grupo"])

    # Capture any extra private keys for future extensibility
    base._extra = {
        k: v for k, v in estado.items()
        if k.startswith("_") and k not in {
            "_paso", "_regla", "_regla_nombre", "_razon",
            "_rango", "_llm_fallback", "_opinion_changed",
            "_fraccion_adoptantes", "_sim_grupo_a", "_sim_grupo_b",
        }
    }

    return base


def historial_a_vis(
    historial: list[dict],
    modelo_activo: str | None = None,
) -> list[VisualizationState]:
    """
    Converts a full simulation history list into VisualizationState objects.

    Args:
        historial:      List of raw state dicts from simular().
        modelo_activo:  Optional model override forwarded to estado_a_vis().

    Returns:
        List of VisualizationState in chronological order.
    """
    return [estado_a_vis(h, modelo_activo) for h in historial]


# ============================================================
# CONVENIENCE EXTRACTORS
# ============================================================

def extraer_opiniones(vis_states: list[VisualizationState]) -> list[float]:
    """Returns the opinion series from a list of VisualizationState."""
    return [vs.opinion for vs in vis_states]


def extraer_fallback_mask(vis_states: list[VisualizationState]) -> list[bool]:
    """Returns a boolean mask of ticks where LLM fallback was active."""
    return [vs.es_fallback for vs in vis_states]


def tiene_algun_fallback(vis_states: list[VisualizationState]) -> bool:
    """True if any tick in the history used LLM fallback."""
    return any(vs.es_fallback for vs in vis_states)
