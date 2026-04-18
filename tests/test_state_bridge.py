"""
Tests for FASE 2.1 — state_bridge.py (VisualizationState adapter).
Verifies:
  1. estado_a_vis() correctly maps all standard keys.
  2. Optional model-specific fields are None when absent.
  3. Model-specific fields are populated when present.
  4. _llm_fallback is correctly exposed as es_fallback.
  5. _opinion_changed is correctly exposed as opinion_changed.
  6. historial_a_vis() returns the right length.
  7. Convenience extractors work correctly.
  8. delta property returns correct value.
"""

import pytest

from state_bridge import (
    VisualizationState,
    estado_a_vis,
    extraer_fallback_mask,
    extraer_opiniones,
    historial_a_vis,
    tiene_algun_fallback,
)


# ── Fixtures ────────────────────────────────────────────────

BASE_TICK = {
    "opinion":           0.65,
    "opinion_prev":      0.60,
    "propaganda":        0.70,
    "confianza":         0.40,
    "pertenencia_grupo": 0.65,
    "_paso":             5,
    "_regla":            2,
    "_regla_nombre":     "memoria",
    "_razon":            "sistema estable",
    "_rango":            "[0, 1] — Probabilístico",
    "_llm_fallback":     False,
    "_opinion_changed":  True,
}

TICK_UMBRAL_HETEROGENEO = {
    **BASE_TICK,
    "_regla_nombre":        "umbral_heterogeneo",
    "_fraccion_adoptantes": 0.42,
}

TICK_HOMOFILIA = {
    **BASE_TICK,
    "_regla_nombre": "homofilia",
    "_sim_grupo_a":  0.88,
    "_sim_grupo_b":  0.12,
}

TICK_FALLBACK = {
    **BASE_TICK,
    "_llm_fallback": True,
    "_opinion_changed": False,
}


class TestEstadoAVis:

    def test_basic_conversion(self):
        vs = estado_a_vis(BASE_TICK)
        assert isinstance(vs, VisualizationState)
        assert vs.paso            == 5
        assert vs.opinion         == pytest.approx(0.65)
        assert vs.opinion_prev    == pytest.approx(0.60)
        assert vs.regla_nombre    == "memoria"
        assert vs.razon           == "sistema estable"
        assert vs.rango           == "[0, 1] — Probabilístico"
        assert vs.es_fallback     is False
        assert vs.opinion_changed is True
        assert vs.llm_regla_id    == 2
        assert vs.pertenencia_grupo == pytest.approx(0.65)

    def test_delta_property(self):
        vs = estado_a_vis(BASE_TICK)
        assert vs.delta == pytest.approx(0.65 - 0.60)

    def test_optional_fields_none_by_default(self):
        vs = estado_a_vis(BASE_TICK)
        assert vs.fraccion_adoptantes is None
        assert vs.sim_grupo_a         is None
        assert vs.sim_grupo_b         is None

    def test_fraccion_adoptantes_populated(self):
        vs = estado_a_vis(TICK_UMBRAL_HETEROGENEO)
        assert vs.fraccion_adoptantes == pytest.approx(0.42)
        assert vs.es_umbral_heterogeneo is True

    def test_homofilia_sims_populated(self):
        vs = estado_a_vis(TICK_HOMOFILIA)
        assert vs.sim_grupo_a == pytest.approx(0.88)
        assert vs.sim_grupo_b == pytest.approx(0.12)
        assert vs.es_homofilia is True

    def test_fallback_flag_mapped(self):
        vs = estado_a_vis(TICK_FALLBACK)
        assert vs.es_fallback     is True
        assert vs.opinion_changed is False

    def test_missing_optional_keys_handled_gracefully(self):
        minimal = {"opinion": 0.5, "propaganda": 0.6}
        vs = estado_a_vis(minimal)
        assert vs.paso           == 0
        assert vs.opinion        == pytest.approx(0.5)
        assert vs.regla_nombre   == "?"
        assert vs.es_fallback    is False
        assert vs.llm_regla_id   is None

    def test_modelo_activo_override(self):
        tick = {**BASE_TICK}
        del tick["_regla_nombre"]
        vs = estado_a_vis(tick, modelo_activo="hk")
        assert vs.regla_nombre == "hk"

    def test_extra_field_captured(self):
        tick = {**BASE_TICK, "_target_nodes": ["A", "B"]}
        vs = estado_a_vis(tick)
        assert "_target_nodes" in vs._extra


class TestHistorialAVis:

    def _make_historial(self, n: int) -> list[dict]:
        return [
            {**BASE_TICK, "_paso": i, "opinion": 0.5 + i * 0.01}
            for i in range(n)
        ]

    def test_correct_length(self):
        h = self._make_historial(10)
        vis = historial_a_vis(h)
        assert len(vis) == 10

    def test_opinions_match(self):
        h = self._make_historial(5)
        vis = historial_a_vis(h)
        for i, vs in enumerate(vis):
            assert vs.opinion == pytest.approx(0.5 + i * 0.01)

    def test_empty_historial(self):
        vis = historial_a_vis([])
        assert vis == []


class TestConvenienceExtractors:

    def _make_vis_list(self):
        ticks = [BASE_TICK, {**BASE_TICK, "_llm_fallback": True}, BASE_TICK]
        return historial_a_vis(ticks)

    def test_extraer_opiniones(self):
        vis = self._make_vis_list()
        ops = extraer_opiniones(vis)
        assert len(ops) == 3
        assert all(isinstance(o, float) for o in ops)

    def test_extraer_fallback_mask(self):
        vis = self._make_vis_list()
        mask = extraer_fallback_mask(vis)
        assert mask == [False, True, False]

    def test_tiene_algun_fallback_true(self):
        vis = self._make_vis_list()
        assert tiene_algun_fallback(vis) is True

    def test_tiene_algun_fallback_false(self):
        vis = historial_a_vis([BASE_TICK, BASE_TICK])
        assert tiene_algun_fallback(vis) is False
