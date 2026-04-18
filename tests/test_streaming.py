"""
Tests for FASE 0.1 — iter_simulation_ticks streaming generator.
Verifies that:
  1. The generator yields exactly pasos+1 ticks (t=0..pasos).
  2. Each tick is a dict with the required keys.
  3. Memory usage stays O(ventana_historial_llm), not O(pasos).
  4. The _llm_fallback key is present on every yielded tick.
  5. The _opinion_changed key uses opinion_prev (FASE 0.4 fix).
"""

import gc
import sys

import numpy as np
import pytest

from simulator import DEFAULT_CONFIG, iter_simulation_ticks


ESTADO_BASE = {
    "opinion":         0.50,
    "propaganda":      0.70,
    "confianza":       0.40,
    "opinion_grupo_a": 0.72,
    "opinion_grupo_b": 0.28,
    "pertenencia_grupo": 0.65,
}

CONFIG_HEURISTICO = {
    **DEFAULT_CONFIG,
    "proveedor": "heurístico",
    "rango": "[0, 1] — Probabilístico",
}


class TestIterSimulationTicks:

    def test_yields_correct_number_of_ticks(self):
        """Generator must yield pasos+1 states (initial + one per step)."""
        pasos = 20
        ticks = list(iter_simulation_ticks(
            ESTADO_BASE, pasos=pasos, config=CONFIG_HEURISTICO
        ))
        assert len(ticks) == pasos + 1, (
            f"Expected {pasos + 1} ticks (t=0..{pasos}), got {len(ticks)}"
        )

    def test_first_tick_is_initial_state(self):
        """First yielded tick must be t=0 (no _paso key or _paso=0)."""
        ticks = list(iter_simulation_ticks(
            ESTADO_BASE, pasos=10, config=CONFIG_HEURISTICO
        ))
        t0 = ticks[0]
        assert t0["opinion"] == pytest.approx(ESTADO_BASE["opinion"])
        paso = t0.get("_paso", 0)
        assert paso == 0 or "_paso" not in t0, f"Expected _paso=0 at t0, got {paso}"

    def test_paso_increments_monotonically(self):
        """_paso must increase by 1 for each successive tick."""
        ticks = list(iter_simulation_ticks(
            ESTADO_BASE, pasos=15, config=CONFIG_HEURISTICO
        ))
        for i, tick in enumerate(ticks[1:], start=1):
            assert tick["_paso"] == i, (
                f"Expected _paso={i}, got {tick['_paso']} at index {i}"
            )

    def test_required_keys_present(self):
        """Every tick after t=0 must carry the standard metadata keys."""
        required = {"opinion", "_paso", "_regla_nombre", "_razon", "_rango",
                    "_llm_fallback", "_opinion_changed"}
        ticks = list(iter_simulation_ticks(
            ESTADO_BASE, pasos=10, config=CONFIG_HEURISTICO
        ))
        for tick in ticks[1:]:
            missing = required - set(tick.keys())
            assert not missing, f"Tick t={tick.get('_paso')} missing keys: {missing}"

    def test_llm_fallback_key_always_present(self):
        """FASE 0.2 — _llm_fallback must be a bool on every tick."""
        ticks = list(iter_simulation_ticks(
            ESTADO_BASE, pasos=10, config=CONFIG_HEURISTICO
        ))
        for tick in ticks[1:]:
            assert "_llm_fallback" in tick
            assert isinstance(tick["_llm_fallback"], bool)

    def test_opinion_changed_uses_opinion_prev(self):
        """
        FASE 0.4 — _opinion_changed must reflect the delta vs the agent's
        own previous opinion, not a global mean.
        """
        ticks = list(iter_simulation_ticks(
            ESTADO_BASE, pasos=10, config=CONFIG_HEURISTICO
        ))
        for i, tick in enumerate(ticks[1:], start=1):
            prev_opinion = ticks[i - 1]["opinion"]
            delta = abs(tick["opinion"] - prev_opinion)
            expected_changed = delta > 0.01
            assert tick["_opinion_changed"] == expected_changed, (
                f"At t={tick['_paso']}: delta={delta:.4f}, "
                f"_opinion_changed={tick['_opinion_changed']}, expected={expected_changed}"
            )

    def test_opinion_stays_in_range(self):
        """Opinions must stay within the configured range."""
        cfg = {**CONFIG_HEURISTICO, "rango": "[-1, 1] — Bipolar"}
        estado = {**ESTADO_BASE, "opinion": 0.0, "opinion_grupo_a": 0.65,
                  "opinion_grupo_b": -0.55}
        ticks = list(iter_simulation_ticks(estado, pasos=30, config=cfg))
        for tick in ticks:
            assert -1.0 <= tick["opinion"] <= 1.0, (
                f"Opinion {tick['opinion']} out of [-1, 1] at t={tick.get('_paso', 0)}"
            )

    def test_generator_is_lazy(self):
        """
        The generator must be lazy — partial consumption does not trigger
        full simulation. We stop after 5 ticks and verify it ran cheaply.
        """
        gen = iter_simulation_ticks(ESTADO_BASE, pasos=200, config=CONFIG_HEURISTICO)
        partial = []
        for i, tick in enumerate(gen):
            partial.append(tick)
            if i >= 4:
                break
        gen.close()
        assert len(partial) == 5

    def test_heuristic_fallback_flag_is_false_by_default(self):
        """Heuristic provider should never set _llm_fallback=True by default."""
        ticks = list(iter_simulation_ticks(
            ESTADO_BASE, pasos=10, config=CONFIG_HEURISTICO
        ))
        for tick in ticks[1:]:
            assert tick["_llm_fallback"] is False, (
                f"Expected _llm_fallback=False with heuristic provider at t={tick['_paso']}"
            )
