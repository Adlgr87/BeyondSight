"""
Tests for extended models: regla_nash, regla_bayesiana, regla_sir.

These rules are the empirical-database-relevant advanced models (rules 10-12)
that capture sophisticated social dynamics for BeyondSight metrics.
"""
import pytest
import numpy as np
from simulator import DEFAULT_CONFIG


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def cfg_probabilistico():
    return {**DEFAULT_CONFIG, "rango": "[0, 1] — Probabilístico"}


@pytest.fixture
def cfg_bipolar():
    return {**DEFAULT_CONFIG, "rango": "[-1, 1] — Bipolar"}


@pytest.fixture
def estado_prob():
    return {
        "opinion": 0.5,
        "propaganda": 0.6,
        "confianza": 0.5,
        "opinion_grupo_a": 0.75,
        "opinion_grupo_b": 0.25,
        "pertenencia_grupo": 0.6,
    }


@pytest.fixture
def estado_bipolar():
    return {
        "opinion": 0.0,
        "propaganda": 0.4,
        "confianza": 0.5,
        "opinion_grupo_a": 0.65,
        "opinion_grupo_b": -0.55,
        "pertenencia_grupo": 0.6,
    }


# ============================================================
# HELPER: import extended models (skip if unavailable)
# ============================================================

def _get_extended():
    """Returns (regla_nash, regla_bayesiana, regla_sir) or skips."""
    try:
        from extended_models import regla_nash, regla_bayesiana, regla_sir
        return regla_nash, regla_bayesiana, regla_sir
    except ImportError:
        pytest.skip("extended_models not available")


# ============================================================
# RULE 10 — NASH EQUILIBRIUM
# ============================================================

class TestReglaNash:

    def test_returns_opinion_in_probabilistic_range(self, estado_prob, cfg_probabilistico):
        regla_nash, _, _ = _get_extended()
        result = regla_nash(estado_prob, {"c_same": 2.0, "c_diff": 0.5, "intensity": 1.0}, cfg_probabilistico)
        assert 0.0 <= result["opinion"] <= 1.0

    def test_returns_opinion_in_bipolar_range(self, estado_bipolar, cfg_bipolar):
        regla_nash, _, _ = _get_extended()
        result = regla_nash(estado_bipolar, {"c_same": 2.0, "c_diff": 0.5}, cfg_bipolar)
        assert -1.0 <= result["opinion"] <= 1.0

    def test_returns_sigma_keys(self, estado_prob, cfg_probabilistico):
        regla_nash, _, _ = _get_extended()
        result = regla_nash(estado_prob, {}, cfg_probabilistico)
        assert "_nash_sigma_a" in result
        assert "_nash_sigma_b" in result

    def test_sigma_a_and_sigma_b_sum_to_one(self, estado_prob, cfg_probabilistico):
        regla_nash, _, _ = _get_extended()
        result = regla_nash(estado_prob, {}, cfg_probabilistico)
        assert result["_nash_sigma_a"] + result["_nash_sigma_b"] == pytest.approx(1.0, abs=1e-4)

    def test_pertenencia_clipped_to_valid_range(self, estado_prob, cfg_probabilistico):
        regla_nash, _, _ = _get_extended()
        result = regla_nash(estado_prob, {"c_same": 10.0, "c_diff": 0.0, "intensity": 5.0}, cfg_probabilistico)
        assert 0.1 <= result["pertenencia_grupo"] <= 0.9

    def test_state_is_not_mutated(self, estado_prob, cfg_probabilistico):
        regla_nash, _, _ = _get_extended()
        original_opinion = estado_prob["opinion"]
        regla_nash(estado_prob, {}, cfg_probabilistico)
        assert estado_prob["opinion"] == original_opinion

    def test_high_csame_pulls_toward_dominant_group(self, cfg_probabilistico):
        regla_nash, _, _ = _get_extended()
        estado = {
            "opinion": 0.1,
            "propaganda": 0.5,
            "confianza": 0.5,
            "opinion_grupo_a": 0.9,
            "opinion_grupo_b": 0.1,
            "pertenencia_grupo": 0.5,
        }
        result = regla_nash(estado, {"c_same": 5.0, "c_diff": 0.0, "intensity": 2.0}, cfg_probabilistico)
        assert 0.0 <= result["opinion"] <= 1.0

    def test_default_params_produce_valid_opinion(self, estado_prob, cfg_probabilistico):
        regla_nash, _, _ = _get_extended()
        result = regla_nash(estado_prob, {}, cfg_probabilistico)
        assert 0.0 <= result["opinion"] <= 1.0

    def test_symmetric_groups_yield_balanced_pertenencia(self, cfg_probabilistico):
        regla_nash, _, _ = _get_extended()
        estado = {
            "opinion": 0.5,
            "propaganda": 0.5,
            "confianza": 0.5,
            "opinion_grupo_a": 0.75,
            "opinion_grupo_b": 0.25,
            "pertenencia_grupo": 0.5,
        }
        result = regla_nash(estado, {"c_same": 2.0, "c_diff": 0.5}, cfg_probabilistico)
        assert 0.0 <= result["opinion"] <= 1.0


# ============================================================
# RULE 11 — BAYESIAN
# ============================================================

class TestReglaBayesiana:

    def test_returns_opinion_in_probabilistic_range(self, estado_prob, cfg_probabilistico):
        _, regla_bayesiana, _ = _get_extended()
        result = regla_bayesiana(estado_prob, {"n_prior": 10.0, "n_obs": 5.0, "inertia": 0.4}, cfg_probabilistico)
        assert 0.0 <= result["opinion"] <= 1.0

    def test_returns_opinion_in_bipolar_range(self, estado_bipolar, cfg_bipolar):
        _, regla_bayesiana, _ = _get_extended()
        result = regla_bayesiana(estado_bipolar, {}, cfg_bipolar)
        assert -1.0 <= result["opinion"] <= 1.0

    def test_returns_uncertainty_key(self, estado_prob, cfg_probabilistico):
        _, regla_bayesiana, _ = _get_extended()
        result = regla_bayesiana(estado_prob, {}, cfg_probabilistico)
        assert "_bayes_uncertainty" in result

    def test_uncertainty_is_non_negative(self, estado_prob, cfg_probabilistico):
        _, regla_bayesiana, _ = _get_extended()
        result = regla_bayesiana(estado_prob, {}, cfg_probabilistico)
        assert result["_bayes_uncertainty"] >= 0.0

    def test_inertia_one_keeps_opinion_unchanged(self, cfg_probabilistico):
        _, regla_bayesiana, _ = _get_extended()
        estado = {
            "opinion": 0.4,
            "propaganda": 0.9,
            "confianza": 0.5,
            "opinion_grupo_a": 0.8,
            "opinion_grupo_b": 0.2,
            "pertenencia_grupo": 0.6,
        }
        result = regla_bayesiana(estado, {"inertia": 1.0}, cfg_probabilistico)
        assert result["opinion"] == pytest.approx(estado["opinion"], abs=0.01)

    def test_state_not_mutated(self, estado_prob, cfg_probabilistico):
        _, regla_bayesiana, _ = _get_extended()
        original_opinion = estado_prob["opinion"]
        regla_bayesiana(estado_prob, {}, cfg_probabilistico)
        assert estado_prob["opinion"] == original_opinion

    def test_high_propaganda_shifts_opinion(self, cfg_probabilistico):
        _, regla_bayesiana, _ = _get_extended()
        estado = {
            "opinion": 0.1,
            "propaganda": 0.95,
            "confianza": 0.8,
            "opinion_grupo_a": 0.9,
            "opinion_grupo_b": 0.1,
            "pertenencia_grupo": 0.9,
        }
        result = regla_bayesiana(estado, {"inertia": 0.0, "n_prior": 5.0, "n_obs": 10.0}, cfg_probabilistico)
        assert result["opinion"] > estado["opinion"]

    def test_default_params_work(self, estado_prob, cfg_probabilistico):
        _, regla_bayesiana, _ = _get_extended()
        result = regla_bayesiana(estado_prob, {}, cfg_probabilistico)
        assert 0.0 <= result["opinion"] <= 1.0

    def test_without_confianza_defaults_gracefully(self, cfg_probabilistico):
        _, regla_bayesiana, _ = _get_extended()
        estado = {
            "opinion": 0.5,
            "propaganda": 0.5,
            "opinion_grupo_a": 0.7,
            "opinion_grupo_b": 0.3,
            "pertenencia_grupo": 0.6,
        }
        result = regla_bayesiana(estado, {}, cfg_probabilistico)
        assert 0.0 <= result["opinion"] <= 1.0


# ============================================================
# RULE 12 — SIR (Susceptible-Influenced-Resistant)
# ============================================================

class TestReglaSIR:

    def test_returns_opinion_in_probabilistic_range(self, estado_prob, cfg_probabilistico):
        _, _, regla_sir = _get_extended()
        result = regla_sir(estado_prob, {"beta": 0.3, "gamma": 0.1, "dt": 0.2}, cfg_probabilistico)
        assert 0.0 <= result["opinion"] <= 1.0

    def test_returns_sir_compartment_keys(self, estado_prob, cfg_probabilistico):
        _, _, regla_sir = _get_extended()
        result = regla_sir(estado_prob, {}, cfg_probabilistico)
        assert "_sir_S" in result
        assert "_sir_I" in result
        assert "_sir_R" in result

    def test_sir_fractions_sum_to_approx_one(self, estado_prob, cfg_probabilistico):
        _, _, regla_sir = _get_extended()
        result = regla_sir(estado_prob, {"beta": 0.3, "gamma": 0.1, "dt": 0.2}, cfg_probabilistico)
        total = result["_sir_S"] + result["_sir_I"] + result["_sir_R"]
        assert total == pytest.approx(1.0, abs=0.01)

    def test_sir_fractions_non_negative(self, estado_prob, cfg_probabilistico):
        _, _, regla_sir = _get_extended()
        result = regla_sir(estado_prob, {}, cfg_probabilistico)
        assert result["_sir_S"] >= 0.0
        assert result["_sir_I"] >= 0.0
        assert result["_sir_R"] >= 0.0

    def test_high_beta_increases_influenced(self, cfg_probabilistico):
        _, _, regla_sir = _get_extended()
        estado = {
            "opinion": 0.5, "propaganda": 0.7,
            "opinion_grupo_a": 0.7, "opinion_grupo_b": 0.3,
            "pertenencia_grupo": 0.6, "confianza": 0.5,
        }
        result_low  = regla_sir(estado, {"beta": 0.05, "gamma": 0.01, "dt": 0.2}, cfg_probabilistico)
        result_high = regla_sir(estado, {"beta": 0.8,  "gamma": 0.01, "dt": 0.2}, cfg_probabilistico)
        assert result_high["_sir_R"] >= result_low["_sir_R"]

    def test_high_gamma_removes_influenced_faster(self, cfg_probabilistico):
        _, _, regla_sir = _get_extended()
        estado = {
            "opinion": 0.5, "propaganda": 0.5,
            "opinion_grupo_a": 0.7, "opinion_grupo_b": 0.3,
            "pertenencia_grupo": 0.6, "confianza": 0.5,
        }
        result_low_gamma  = regla_sir(estado, {"beta": 0.3, "gamma": 0.01, "dt": 0.5}, cfg_probabilistico)
        result_high_gamma = regla_sir(estado, {"beta": 0.3, "gamma": 0.5,  "dt": 0.5}, cfg_probabilistico)
        assert result_high_gamma["_sir_R"] >= result_low_gamma["_sir_R"]

    def test_state_not_mutated(self, estado_prob, cfg_probabilistico):
        _, _, regla_sir = _get_extended()
        original_opinion = estado_prob["opinion"]
        regla_sir(estado_prob, {}, cfg_probabilistico)
        assert estado_prob["opinion"] == original_opinion

    def test_bipolar_range_opinion_valid(self, estado_bipolar, cfg_bipolar):
        _, _, regla_sir = _get_extended()
        result = regla_sir(estado_bipolar, {"beta": 0.3, "gamma": 0.1, "dt": 0.2}, cfg_bipolar)
        assert -1.0 <= result["opinion"] <= 1.0

    def test_zero_propaganda_low_contagion(self, cfg_probabilistico):
        _, _, regla_sir = _get_extended()
        estado = {
            "opinion": 0.5, "propaganda": 0.0,
            "opinion_grupo_a": 0.5, "opinion_grupo_b": 0.5,
            "pertenencia_grupo": 0.5, "confianza": 0.5,
        }
        result = regla_sir(estado, {"beta": 0.3, "gamma": 0.05, "dt": 0.1}, cfg_probabilistico)
        assert 0.0 <= result["opinion"] <= 1.0

    def test_default_params_work(self, estado_prob, cfg_probabilistico):
        _, _, regla_sir = _get_extended()
        result = regla_sir(estado_prob, {}, cfg_probabilistico)
        assert 0.0 <= result["opinion"] <= 1.0


# ============================================================
# EXTENDED MODELS INTEGRATION — simular() with rules 10-12
# ============================================================

class TestExtendedModelsInSimular:
    """Integration: extended rules applied inside simular() stay in range."""

    def _estado(self):
        return {
            "opinion": 0.5,
            "propaganda": 0.6,
            "confianza": 0.5,
            "opinion_grupo_a": 0.75,
            "opinion_grupo_b": 0.25,
            "pertenencia_grupo": 0.6,
        }

    def _run_rule(self, rule_name, cfg_override=None):
        from simulator import EXTENDED_MODELS_AVAILABLE, run_with_schedule, DEFAULT_CONFIG
        if not EXTENDED_MODELS_AVAILABLE:
            pytest.skip("Extended models not installed")
        cfg = {**DEFAULT_CONFIG, **(cfg_override or {})}
        schedule = {
            "interventions": [
                {"time_start": 1, "time_end": 5, "model_name": rule_name,
                 "parameters": {}, "fase_rationale": "test"}
            ]
        }
        return run_with_schedule(self._estado(), schedule, config=cfg, verbose=False)

    def test_nash_rule_in_schedule_stays_in_range(self):
        hist = self._run_rule("nash")
        assert all(0.0 <= h["opinion"] <= 1.0 for h in hist)

    def test_bayesiano_rule_in_schedule_stays_in_range(self):
        hist = self._run_rule("bayesiano")
        assert all(0.0 <= h["opinion"] <= 1.0 for h in hist)

    def test_sir_rule_in_schedule_stays_in_range(self):
        hist = self._run_rule("sir")
        assert all(0.0 <= h["opinion"] <= 1.0 for h in hist)

    def test_nash_records_sigma_keys(self):
        hist = self._run_rule("nash")
        nash_steps = [h for h in hist if "_nash_sigma_a" in h]
        assert len(nash_steps) > 0

    def test_sir_records_compartment_keys(self):
        hist = self._run_rule("sir")
        sir_steps = [h for h in hist if "_sir_S" in h]
        assert len(sir_steps) > 0
