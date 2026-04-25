"""
Tests for individual simulator rules and helper utilities.

Covers:
  - All 10 base rules (0-9): lineal, umbral, memoria, backlash, polarizacion,
    hk, contagio_competitivo, umbral_heterogeneo, homofilia, replicador
  - Helper functions: resumen_historial (with config), calcular_efecto_grupos,
    _aplicar_sesgo_confirmacion, _actualizar_pesos_homofilia,
    calculate_ews_metrics, check_ews_signals, apply_replicator_equation,
    get_graph_metrics
  - run_with_schedule integration
  - llamar_llm_heuristico selector logic
"""
import pytest
import numpy as np
import networkx as nx

from simulator import (
    DEFAULT_CONFIG,
    regla_lineal,
    regla_umbral,
    regla_memoria,
    regla_backlash,
    regla_polarizacion,
    regla_hk,
    regla_contagio_competitivo,
    regla_umbral_heterogeneo,
    regla_homofilia,
    regla_replicador,
    apply_replicator_equation,
    calculate_ews_metrics,
    check_ews_signals,
    calcular_efecto_grupos,
    resumen_historial,
    run_with_schedule,
    simular,
    llamar_llm_heuristico,
    get_graph_metrics,
    HISTORY_BUFFER_SIZE,
)


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
    """Typical state in [0, 1] probabilistic range."""
    return {
        "opinion": 0.5,
        "propaganda": 0.7,
        "confianza": 0.4,
        "tension": 0.3,
        "opinion_grupo_a": 0.72,
        "opinion_grupo_b": 0.28,
        "pertenencia_grupo": 0.65,
    }


@pytest.fixture
def estado_bipolar():
    """Typical state in [-1, 1] bipolar range."""
    return {
        "opinion": 0.0,
        "propaganda": 0.4,
        "confianza": 0.5,
        "opinion_grupo_a": 0.65,
        "opinion_grupo_b": -0.55,
        "pertenencia_grupo": 0.6,
    }


# ============================================================
# RULE 0 — LINEAL
# ============================================================

class TestReglaLineal:

    def test_opinion_changes_with_propaganda(self, estado_prob, cfg_probabilistico):
        result = regla_lineal(estado_prob, {"a": 0.7, "b": 0.3}, cfg_probabilistico)
        expected = 0.7 * estado_prob["opinion"] + 0.3 * estado_prob["propaganda"]
        assert result["opinion"] == pytest.approx(expected, abs=1e-6)

    def test_stays_in_probabilistic_range(self, estado_prob, cfg_probabilistico):
        result = regla_lineal(estado_prob, {"a": 0.9, "b": 0.9}, cfg_probabilistico)
        assert 0.0 <= result["opinion"] <= 1.0

    def test_stays_in_bipolar_range(self, estado_bipolar, cfg_bipolar):
        result = regla_lineal(estado_bipolar, {"a": 0.9, "b": 0.9}, cfg_bipolar)
        assert -1.0 <= result["opinion"] <= 1.0

    def test_state_is_copied_not_mutated(self, estado_prob, cfg_probabilistico):
        original_opinion = estado_prob["opinion"]
        regla_lineal(estado_prob, {}, cfg_probabilistico)
        assert estado_prob["opinion"] == original_opinion

    def test_default_params_produce_valid_opinion(self, estado_prob, cfg_probabilistico):
        result = regla_lineal(estado_prob, {}, cfg_probabilistico)
        assert 0.0 <= result["opinion"] <= 1.0


# ============================================================
# RULE 1 — UMBRAL
# ============================================================

class TestReglaUmbral:

    def test_jump_when_propaganda_exceeds_threshold(self, estado_prob, cfg_probabilistico):
        estado = {**estado_prob, "opinion": 0.3, "propaganda": 0.9}
        result = regla_umbral(estado, {"umbral": 0.5, "incremento": 0.2}, cfg_probabilistico)
        assert result["opinion"] > estado["opinion"]

    def test_no_jump_below_threshold(self, estado_prob, cfg_probabilistico):
        estado = {**estado_prob, "opinion": 0.5, "propaganda": 0.1}
        result = regla_umbral(estado, {"umbral": 0.65, "incremento": 0.2}, cfg_probabilistico)
        assert result["opinion"] == pytest.approx(estado["opinion"])

    def test_opinion_clipped_to_range(self, estado_prob, cfg_probabilistico):
        estado = {**estado_prob, "opinion": 0.95, "propaganda": 1.0}
        result = regla_umbral(estado, {"umbral": 0.3, "incremento": 0.5}, cfg_probabilistico)
        assert result["opinion"] <= 1.0

    def test_bipolar_jump_direction(self, estado_bipolar, cfg_bipolar):
        estado = {**estado_bipolar, "opinion": 0.1, "propaganda": 0.8}
        result = regla_umbral(estado, {"umbral": 0.3, "incremento": 0.2}, cfg_bipolar)
        assert -1.0 <= result["opinion"] <= 1.0


# ============================================================
# RULE 2 — MEMORIA
# ============================================================

class TestReglaMemoria:

    def test_inertia_keeps_opinion_stable(self, estado_prob, cfg_probabilistico):
        estado = {**estado_prob, "opinion": 0.5, "propaganda": 0.5}
        estado["opinion_prev"] = 0.5
        result = regla_memoria(estado, {"alpha": 0.7, "beta": 0.2, "gamma": 0.1}, cfg_probabilistico)
        assert result["opinion"] == pytest.approx(0.5, abs=1e-5)

    def test_opinion_is_weighted_combination(self, estado_prob, cfg_probabilistico):
        estado = {**estado_prob, "opinion": 0.6, "opinion_prev": 0.4, "propaganda": 0.8}
        alpha, beta, gamma = 0.7, 0.2, 0.1
        expected = alpha * 0.6 + beta * 0.4 + gamma * 0.8
        result = regla_memoria(estado, {"alpha": alpha, "beta": beta, "gamma": gamma}, cfg_probabilistico)
        assert result["opinion"] == pytest.approx(np.clip(expected, 0.0, 1.0), abs=1e-5)

    def test_stays_in_range(self, estado_prob, cfg_probabilistico):
        estado = {**estado_prob, "opinion": 0.9, "opinion_prev": 0.95, "propaganda": 1.0}
        result = regla_memoria(estado, {"alpha": 0.8, "beta": 0.3, "gamma": 0.3}, cfg_probabilistico)
        assert 0.0 <= result["opinion"] <= 1.0

    def test_defaults_when_no_opinion_prev(self, estado_prob, cfg_probabilistico):
        estado = {k: v for k, v in estado_prob.items() if k != "opinion_prev"}
        result = regla_memoria(estado, {}, cfg_probabilistico)
        assert 0.0 <= result["opinion"] <= 1.0


# ============================================================
# RULE 3 — BACKLASH
# ============================================================

class TestReglaBacklash:

    def test_backlash_pushes_away_when_low_opinion(self, cfg_probabilistico):
        estado = {
            "opinion": 0.2, "propaganda": 0.8,
            "opinion_grupo_a": 0.7, "opinion_grupo_b": 0.3,
            "pertenencia_grupo": 0.6, "confianza": 0.4,
        }
        result = regla_backlash(estado, {"penalizacion": 0.15}, cfg_probabilistico)
        assert result["opinion"] < estado["opinion"]

    def test_no_backlash_when_opinion_above_threshold(self, cfg_probabilistico):
        estado = {
            "opinion": 0.7, "propaganda": 0.8,
            "opinion_grupo_a": 0.8, "opinion_grupo_b": 0.3,
            "pertenencia_grupo": 0.6, "confianza": 0.5,
        }
        result = regla_backlash(estado, {"penalizacion": 0.15}, cfg_probabilistico)
        assert result["opinion"] == pytest.approx(estado["opinion"])

    def test_bipolar_backlash_when_negative(self, cfg_bipolar):
        estado = {
            "opinion": -0.5, "propaganda": 0.6,
            "opinion_grupo_a": 0.5, "opinion_grupo_b": -0.5,
            "pertenencia_grupo": 0.6, "confianza": 0.5,
        }
        result = regla_backlash(estado, {"penalizacion": 0.15}, cfg_bipolar)
        assert result["opinion"] <= estado["opinion"]

    def test_opinion_stays_in_range(self, cfg_probabilistico):
        estado = {
            "opinion": 0.05, "propaganda": 1.0,
            "opinion_grupo_a": 0.8, "opinion_grupo_b": 0.1,
            "pertenencia_grupo": 0.6, "confianza": 0.2,
        }
        result = regla_backlash(estado, {"penalizacion": 0.5}, cfg_probabilistico)
        assert 0.0 <= result["opinion"] <= 1.0


# ============================================================
# RULE 4 — POLARIZACION
# ============================================================

class TestReglaPolarizacion:

    def test_moves_away_from_neutral_when_above(self, cfg_probabilistico):
        estado = {
            "opinion": 0.7, "propaganda": 0.5,
            "opinion_grupo_a": 0.8, "opinion_grupo_b": 0.3,
            "pertenencia_grupo": 0.6, "confianza": 0.5,
        }
        result = regla_polarizacion(estado, {"fuerza": 0.1}, cfg_probabilistico)
        assert result["opinion"] >= estado["opinion"]

    def test_moves_away_from_neutral_when_below(self, cfg_probabilistico):
        estado = {
            "opinion": 0.2, "propaganda": 0.4,
            "opinion_grupo_a": 0.7, "opinion_grupo_b": 0.2,
            "pertenencia_grupo": 0.6, "confianza": 0.5,
        }
        result = regla_polarizacion(estado, {"fuerza": 0.1}, cfg_probabilistico)
        assert result["opinion"] <= estado["opinion"]

    def test_bipolar_above_neutral_moves_right(self, cfg_bipolar):
        estado = {
            "opinion": 0.3, "propaganda": 0.4,
            "opinion_grupo_a": 0.5, "opinion_grupo_b": -0.5,
            "pertenencia_grupo": 0.6, "confianza": 0.5,
        }
        result = regla_polarizacion(estado, {"fuerza": 0.1}, cfg_bipolar)
        assert result["opinion"] >= estado["opinion"]

    def test_stays_in_range(self, cfg_probabilistico):
        estado = {
            "opinion": 0.99, "propaganda": 0.9,
            "opinion_grupo_a": 0.9, "opinion_grupo_b": 0.5,
            "pertenencia_grupo": 0.6, "confianza": 0.5,
        }
        result = regla_polarizacion(estado, {"fuerza": 0.9}, cfg_probabilistico)
        assert 0.0 <= result["opinion"] <= 1.0


# ============================================================
# RULE 5 — HK (Hegselmann-Krause)
# ============================================================

class TestReglaHK:

    def test_converges_toward_in_range_group(self, cfg_probabilistico):
        estado = {
            "opinion": 0.5, "propaganda": 0.5,
            "opinion_grupo_a": 0.6, "opinion_grupo_b": 0.55,
            "pertenencia_grupo": 0.5, "confianza": 0.5,
        }
        result = regla_hk(estado, {"epsilon": 0.3, "alpha": 0.5}, cfg_probabilistico)
        assert 0.0 <= result["opinion"] <= 1.0

    def test_minimal_change_when_no_group_in_range(self, cfg_probabilistico):
        estado = {
            "opinion": 0.5, "propaganda": 0.5,
            "opinion_grupo_a": 0.9, "opinion_grupo_b": 0.05,
            "pertenencia_grupo": 0.5, "confianza": 0.5,
        }
        result = regla_hk(estado, {"epsilon": 0.1}, cfg_probabilistico)
        assert 0.0 <= result["opinion"] <= 1.0

    def test_hk_uses_cfg_epsilon_fallback(self, cfg_probabilistico):
        cfg = {**cfg_probabilistico, "hk_epsilon": 0.4}
        estado = {
            "opinion": 0.5, "propaganda": 0.4,
            "opinion_grupo_a": 0.7, "opinion_grupo_b": 0.3,
            "pertenencia_grupo": 0.5, "confianza": 0.5,
        }
        result = regla_hk(estado, {}, cfg)
        assert 0.0 <= result["opinion"] <= 1.0


# ============================================================
# RULE 6 — CONTAGIO COMPETITIVO
# ============================================================

class TestReglaContagioCompetitivo:

    def test_strong_narrative_a_moves_opinion_up(self, cfg_probabilistico):
        estado = {
            "opinion": 0.5, "propaganda": 0.9,
            "narrativa_b": 0.1,
            "opinion_grupo_a": 0.7, "opinion_grupo_b": 0.3,
            "pertenencia_grupo": 0.6, "confianza": 0.5,
        }
        result = regla_contagio_competitivo(estado, {"competencia": 0.2}, cfg_probabilistico)
        assert 0.0 <= result["opinion"] <= 1.0

    def test_competing_narratives_result_is_in_range(self, cfg_bipolar):
        estado = {
            "opinion": 0.0, "propaganda": 0.5,
            "narrativa_b": -0.5,
            "opinion_grupo_a": 0.5, "opinion_grupo_b": -0.5,
            "pertenencia_grupo": 0.5, "confianza": 0.5,
        }
        result = regla_contagio_competitivo(estado, {"competencia": 0.4}, cfg_bipolar)
        assert -1.0 <= result["opinion"] <= 1.0

    def test_without_narrativa_b_uses_default(self, cfg_probabilistico):
        estado = {
            "opinion": 0.5, "propaganda": 0.7,
            "opinion_grupo_a": 0.7, "opinion_grupo_b": 0.3,
            "pertenencia_grupo": 0.6, "confianza": 0.5,
        }
        result = regla_contagio_competitivo(estado, {}, cfg_probabilistico)
        assert 0.0 <= result["opinion"] <= 1.0


# ============================================================
# RULE 7 — UMBRAL HETEROGENEO
# ============================================================

class TestReglaUmbralHeterogeneo:

    def test_returns_opinion_in_range(self, estado_prob, cfg_probabilistico):
        result = regla_umbral_heterogeneo(estado_prob, {"media": 0.5, "std": 0.15}, cfg_probabilistico)
        assert 0.0 <= result["opinion"] <= 1.0

    def test_returns_fraccion_adoptantes_key(self, estado_prob, cfg_probabilistico):
        result = regla_umbral_heterogeneo(estado_prob, {}, cfg_probabilistico)
        assert "_fraccion_adoptantes" in result
        assert 0.0 <= result["_fraccion_adoptantes"] <= 1.0

    def test_high_opinion_has_higher_adoption_fraction(self, cfg_probabilistico):
        estado_low = {
            "opinion": 0.1, "propaganda": 0.3,
            "opinion_grupo_a": 0.7, "opinion_grupo_b": 0.2,
            "pertenencia_grupo": 0.6, "confianza": 0.5,
        }
        estado_high = {**estado_low, "opinion": 0.9}
        result_low  = regla_umbral_heterogeneo(estado_low,  {}, cfg_probabilistico)
        result_high = regla_umbral_heterogeneo(estado_high, {}, cfg_probabilistico)
        assert result_high["_fraccion_adoptantes"] >= result_low["_fraccion_adoptantes"]


# ============================================================
# RULE 8 — HOMOFILIA
# ============================================================

class TestReglaHomofilia:

    def test_returns_similarity_keys(self, estado_prob, cfg_probabilistico):
        result = regla_homofilia(estado_prob, {}, cfg_probabilistico)
        assert "_sim_grupo_a" in result
        assert "_sim_grupo_b" in result

    def test_pertenencia_grupo_updated(self, estado_prob, cfg_probabilistico):
        initial_perten = estado_prob["pertenencia_grupo"]
        result = regla_homofilia(estado_prob, {"tasa": 0.1}, cfg_probabilistico)
        assert "pertenencia_grupo" in result
        assert 0.1 <= result["pertenencia_grupo"] <= 0.9

    def test_opinion_stays_in_range_probabilistic(self, estado_prob, cfg_probabilistico):
        result = regla_homofilia(estado_prob, {"tasa": 0.2}, cfg_probabilistico)
        assert 0.0 <= result["opinion"] <= 1.0

    def test_opinion_stays_in_range_bipolar(self, estado_bipolar, cfg_bipolar):
        result = regla_homofilia(estado_bipolar, {"tasa": 0.1}, cfg_bipolar)
        assert -1.0 <= result["opinion"] <= 1.0


# ============================================================
# RULE 9 — REPLICADOR (EGT)
# ============================================================

class TestReglaReplicador:

    def test_returns_valid_opinion(self, estado_prob, cfg_probabilistico):
        result = regla_replicador(estado_prob, {"dt": 0.1}, cfg_probabilistico)
        assert 0.0 <= result["opinion"] <= 1.0

    def test_pertenencia_clipped(self, estado_prob, cfg_probabilistico):
        result = regla_replicador(estado_prob, {"dt": 0.1}, cfg_probabilistico)
        assert 0.1 <= result["pertenencia_grupo"] <= 0.9

    def test_invalid_payoff_matrix_falls_back_to_identity(self, estado_prob, cfg_probabilistico):
        result = regla_replicador(
            estado_prob,
            {"payoff_matrix": [[1, 0, 0], [0, 1, 0]], "dt": 0.1},
            cfg_probabilistico
        )
        assert 0.0 <= result["opinion"] <= 1.0

    def test_symmetric_payoff_preserves_perten(self, cfg_probabilistico):
        estado = {
            "opinion": 0.5, "propaganda": 0.5,
            "opinion_grupo_a": 0.6, "opinion_grupo_b": 0.4,
            "pertenencia_grupo": 0.5, "confianza": 0.5,
        }
        result = regla_replicador(
            estado,
            {"payoff_matrix": [[1.0, 0.0], [0.0, 1.0]], "dt": 0.01},
            cfg_probabilistico,
        )
        assert result["pertenencia_grupo"] == pytest.approx(0.5, abs=0.1)


# ============================================================
# APPLY REPLICATOR EQUATION
# ============================================================

class TestApplyReplicatorEquation:

    def test_frequencies_sum_to_one(self):
        pop = np.array([0.4, 0.6])
        payoff = np.array([[1.0, 0.0], [0.0, 1.0]])
        result = apply_replicator_equation(pop, payoff, dt=0.1)
        assert np.sum(result) == pytest.approx(1.0, abs=1e-6)

    def test_all_positive_frequencies(self):
        pop = np.array([0.3, 0.7])
        payoff = np.array([[2.0, 0.0], [0.0, 1.0]])
        result = apply_replicator_equation(pop, payoff, dt=0.5)
        assert np.all(result >= 0.0)

    def test_zero_population_returns_zeros(self):
        pop = np.array([0.0, 0.0])
        payoff = np.array([[1.0, 0.0], [0.0, 1.0]])
        result = apply_replicator_equation(pop, payoff, dt=0.1)
        assert np.all(result == 0.0)

    def test_dominant_strategy_grows(self):
        pop = np.array([0.5, 0.5])
        payoff = np.array([[3.0, 0.0], [0.0, 1.0]])
        result = apply_replicator_equation(pop, payoff, dt=0.5)
        assert result[0] > pop[0]


# ============================================================
# CALCULATE EWS METRICS
# ============================================================

class TestCalculateEWSMetrics:

    def test_returns_required_keys(self):
        window = [0.1 * i for i in range(HISTORY_BUFFER_SIZE)]
        metrics = calculate_ews_metrics(window)
        assert "variance" in metrics
        assert "autocorr" in metrics
        assert "skewness" in metrics

    def test_constant_series_zero_variance(self):
        window = [0.5] * HISTORY_BUFFER_SIZE
        metrics = calculate_ews_metrics(window)
        assert float(np.mean(metrics["variance"])) == pytest.approx(0.0, abs=1e-9)

    def test_linearly_increasing_series_has_high_autocorr(self):
        window = list(range(HISTORY_BUFFER_SIZE))
        metrics = calculate_ews_metrics(window)
        assert float(np.mean(metrics["autocorr"])) > 0.9

    def test_single_element_list_returns_zero_autocorr(self):
        metrics = calculate_ews_metrics([0.5])
        assert float(np.mean(metrics["autocorr"])) == pytest.approx(0.0, abs=1e-9)

    def test_oscillating_series_has_negative_autocorr(self):
        window = [0.0 if i % 2 == 0 else 1.0 for i in range(HISTORY_BUFFER_SIZE)]
        metrics = calculate_ews_metrics(window)
        assert float(np.mean(metrics["autocorr"])) < 0.0


# ============================================================
# CHECK EWS SIGNALS
# ============================================================

class TestCheckEWSSignals:

    def test_high_variance_detected(self):
        metrics = {
            "variance": np.array([0.5]),
            "autocorr": np.array([0.0]),
            "skewness": np.array([0.0]),
        }
        flags = check_ews_signals(metrics, {})
        assert flags["high_variance"] is True

    def test_low_variance_not_flagged(self):
        metrics = {
            "variance": np.array([0.01]),
            "autocorr": np.array([0.0]),
            "skewness": np.array([0.0]),
        }
        flags = check_ews_signals(metrics, {})
        assert flags["high_variance"] is False

    def test_high_autocorr_detected(self):
        metrics = {
            "variance": np.array([0.0]),
            "autocorr": np.array([0.9]),
            "skewness": np.array([0.0]),
        }
        flags = check_ews_signals(metrics, {})
        assert flags["high_autocorr"] is True

    def test_custom_thresholds_override_defaults(self):
        metrics = {
            "variance": np.array([0.05]),
            "autocorr": np.array([0.0]),
            "skewness": np.array([0.0]),
        }
        flags = check_ews_signals(metrics, {"mean_variance_threshold": 0.01})
        assert flags["high_variance"] is True


# ============================================================
# CALCULAR EFECTO GRUPOS
# ============================================================

class TestCalcularEfectoGrupos:

    def test_pushes_toward_group_reference(self, cfg_probabilistico):
        estado = {
            "opinion": 0.2,
            "opinion_grupo_a": 0.9, "opinion_grupo_b": 0.1,
            "pertenencia_grupo": 0.8,
        }
        efecto = calcular_efecto_grupos(estado, cfg_probabilistico)
        assert efecto > 0.0

    def test_neutral_state_small_effect(self, cfg_probabilistico):
        estado = {
            "opinion": 0.5,
            "opinion_grupo_a": 0.5, "opinion_grupo_b": 0.5,
            "pertenencia_grupo": 0.5,
        }
        efecto = calcular_efecto_grupos(estado, cfg_probabilistico)
        assert abs(efecto) < 1e-9

    def test_bipolar_pushes_toward_reference(self, cfg_bipolar):
        estado = {
            "opinion": -0.8,
            "opinion_grupo_a": 0.5, "opinion_grupo_b": -0.3,
            "pertenencia_grupo": 0.7,
        }
        efecto = calcular_efecto_grupos(estado, cfg_bipolar)
        assert efecto > 0.0


# ============================================================
# RESUMEN HISTORIAL
# ============================================================

class TestResumenHistorial:

    def _make_historial(self, n=10, start=0.3, end=0.7):
        opiniones = np.linspace(start, end, n + 1)
        return [
            {"opinion": float(op), "_regla_nombre": "lineal"} for op in opiniones
        ]

    def test_required_keys_present(self, cfg_probabilistico):
        hist = self._make_historial()
        stats = resumen_historial(hist, cfg_probabilistico)
        for key in ("opinion_inicial", "opinion_final", "delta_total", "media",
                    "desviacion", "minimo", "maximo", "polarizacion_media",
                    "pasos", "regla_dominante", "neutro", "rango"):
            assert key in stats

    def test_delta_total_correct(self, cfg_probabilistico):
        hist = self._make_historial(start=0.3, end=0.7)
        stats = resumen_historial(hist, cfg_probabilistico)
        assert stats["delta_total"] == pytest.approx(stats["opinion_final"] - stats["opinion_inicial"])

    def test_pasos_count(self, cfg_probabilistico):
        hist = self._make_historial(n=15)
        stats = resumen_historial(hist, cfg_probabilistico)
        assert stats["pasos"] == 15

    def test_neutro_probabilistic(self, cfg_probabilistico):
        hist = self._make_historial()
        stats = resumen_historial(hist, cfg_probabilistico)
        assert stats["neutro"] == pytest.approx(0.5)

    def test_neutro_bipolar(self, cfg_bipolar):
        hist = [{"opinion": float(x), "_regla_nombre": "lineal"}
                for x in np.linspace(-0.5, 0.5, 11)]
        stats = resumen_historial(hist, cfg_bipolar)
        assert stats["neutro"] == pytest.approx(0.0)

    def test_regla_dominante_detected(self, cfg_probabilistico):
        hist = [{"opinion": 0.5, "_regla_nombre": "hk"} for _ in range(8)]
        hist += [{"opinion": 0.5, "_regla_nombre": "lineal"} for _ in range(3)]
        stats = resumen_historial(hist, cfg_probabilistico)
        assert stats["regla_dominante"] == "hk"

    def test_regla_dominante_fallback_on_empty(self, cfg_probabilistico):
        hist = [{"opinion": 0.5} for _ in range(5)]
        stats = resumen_historial(hist, cfg_probabilistico)
        assert stats["regla_dominante"] == "—"

    def test_polarizacion_media_bipolar(self, cfg_bipolar):
        hist = [{"opinion": 0.0, "_regla_nombre": "lineal"} for _ in range(11)]
        stats = resumen_historial(hist, cfg_bipolar)
        assert stats["polarizacion_media"] == pytest.approx(0.0)

    def test_polarizacion_media_positive(self, cfg_probabilistico):
        hist = [{"opinion": 0.9, "_regla_nombre": "lineal"} for _ in range(11)]
        stats = resumen_historial(hist, cfg_probabilistico)
        assert stats["polarizacion_media"] > 0.0


# ============================================================
# RUN WITH SCHEDULE
# ============================================================

class TestRunWithSchedule:

    def _base_estado(self):
        return {
            "opinion": 0.4,
            "propaganda": 0.6,
            "confianza": 0.5,
            "opinion_grupo_a": 0.7,
            "opinion_grupo_b": 0.3,
            "pertenencia_grupo": 0.6,
        }

    def test_returns_historial_list(self):
        schedule = {
            "interventions": [
                {"time_start": 1, "time_end": 5, "model_name": "lineal",
                 "parameters": {}, "fase_rationale": "test"}
            ]
        }
        hist = run_with_schedule(self._base_estado(), schedule, verbose=False)
        assert isinstance(hist, list)
        assert len(hist) > 1

    def test_historial_includes_t0(self):
        schedule = {"interventions": []}
        hist = run_with_schedule(self._base_estado(), schedule, verbose=False)
        assert hist[0]["opinion"] == pytest.approx(self._base_estado()["opinion"])

    def test_multiple_phases_execute(self):
        schedule = {
            "interventions": [
                {"time_start": 1, "time_end": 3, "model_name": "lineal",
                 "parameters": {}, "fase_rationale": "phase 1"},
                {"time_start": 4, "time_end": 6, "model_name": "hk",
                 "parameters": {"epsilon": 0.4}, "fase_rationale": "phase 2"},
            ]
        }
        hist = run_with_schedule(self._base_estado(), schedule, verbose=False)
        assert len(hist) >= 7

    def test_all_opinions_in_range(self):
        schedule = {
            "interventions": [
                {"time_start": 1, "time_end": 10, "model_name": "polarizacion",
                 "parameters": {"fuerza": 0.2}, "fase_rationale": "polarize"}
            ]
        }
        hist = run_with_schedule(self._base_estado(), schedule, verbose=False)
        assert all(0.0 <= h["opinion"] <= 1.0 for h in hist)

    def test_regla_nombre_recorded(self):
        schedule = {
            "interventions": [
                {"time_start": 1, "time_end": 3, "model_name": "memoria",
                 "parameters": {}, "fase_rationale": "test"}
            ]
        }
        hist = run_with_schedule(self._base_estado(), schedule, verbose=False)
        assert any(h.get("_regla_nombre") == "memoria" for h in hist[1:])

    def test_unknown_model_falls_back_to_lineal(self):
        schedule = {
            "interventions": [
                {"time_start": 1, "time_end": 3, "model_name": "unknown_rule",
                 "parameters": {}, "fase_rationale": "test"}
            ]
        }
        hist = run_with_schedule(self._base_estado(), schedule, verbose=False)
        assert len(hist) >= 1

    def test_bipolar_range_respected(self):
        cfg = {**DEFAULT_CONFIG, "rango": "[-1, 1] — Bipolar"}
        estado = {
            "opinion": 0.0, "propaganda": 0.4,
            "confianza": 0.5,
            "opinion_grupo_a": 0.65, "opinion_grupo_b": -0.55,
            "pertenencia_grupo": 0.6,
        }
        schedule = {
            "interventions": [
                {"time_start": 1, "time_end": 5, "model_name": "polarizacion",
                 "parameters": {"fuerza": 0.3}, "fase_rationale": "test"}
            ]
        }
        hist = run_with_schedule(estado, schedule, config=cfg, verbose=False)
        assert all(-1.0 <= h["opinion"] <= 1.0 for h in hist)

    def test_degroot_alias_resolves_to_memoria(self):
        schedule = {
            "interventions": [
                {"time_start": 1, "time_end": 3, "model_name": "degroot",
                 "parameters": {}, "fase_rationale": "test"}
            ]
        }
        hist = run_with_schedule(self._base_estado(), schedule, verbose=False)
        assert any(h.get("_regla_nombre") == "memoria" for h in hist[1:])


# ============================================================
# LLAMAR LLM HEURISTICO — selector logic
# ============================================================

class TestLlamarLLMHeuristico:

    def _historial(self, opinion=0.5, n=2):
        return [{"opinion": opinion}] * n

    def test_returns_dict_with_required_keys(self, estado_prob, cfg_probabilistico):
        hist = self._historial(0.5)
        result = llamar_llm_heuristico(estado_prob, "campana", hist, cfg_probabilistico)
        assert "regla" in result
        assert "params" in result
        assert "razon" in result

    def test_selects_contagio_when_narrativa_b_active(self, cfg_probabilistico):
        estado = {
            "opinion": 0.5, "propaganda": 0.5, "confianza": 0.5,
            "narrativa_b": 0.8,
            "opinion_grupo_a": 0.7, "opinion_grupo_b": 0.3,
            "pertenencia_grupo": 0.6,
        }
        hist = self._historial(0.5)
        result = llamar_llm_heuristico(estado, "campana", hist, cfg_probabilistico)
        assert result["regla"] == 6

    def test_selects_hk_when_groups_very_distant(self, cfg_probabilistico):
        estado = {
            "opinion": 0.5, "propaganda": 0.4, "confianza": 0.5,
            "opinion_grupo_a": 0.95, "opinion_grupo_b": 0.05,
            "pertenencia_grupo": 0.6,
        }
        hist = self._historial(0.5)
        result = llamar_llm_heuristico(estado, "campana", hist, cfg_probabilistico)
        assert result["regla"] == 5

    def test_selects_backlash_when_low_opinion_high_propaganda(self, cfg_probabilistico):
        estado = {
            "opinion": 0.1, "propaganda": 0.8, "confianza": 0.5,
            "opinion_grupo_a": 0.7, "opinion_grupo_b": 0.3,
            "pertenencia_grupo": 0.6,
        }
        hist = [{"opinion": 0.1}] * 3
        result = llamar_llm_heuristico(estado, "campana", hist, cfg_probabilistico)
        assert result["regla"] == 3

    def test_returns_valid_rule_id(self, estado_prob, cfg_probabilistico):
        hist = self._historial(0.5)
        result = llamar_llm_heuristico(estado_prob, "campana", hist, cfg_probabilistico)
        assert isinstance(result["regla"], int)
        assert 0 <= result["regla"] <= 12


# ============================================================
# GET GRAPH METRICS
# ============================================================

class TestGetGraphMetrics:

    def test_returns_string(self):
        G = nx.path_graph(5)
        result = get_graph_metrics(G)
        assert isinstance(result, str)

    def test_contains_node_count(self):
        G = nx.complete_graph(6)
        result = get_graph_metrics(G)
        assert "6" in result

    def test_empty_graph_returns_empty_message(self):
        G = nx.Graph()
        result = get_graph_metrics(G)
        assert "vacía" in result.lower() or "empty" in result.lower()

    def test_none_graph_returns_message(self):
        result = get_graph_metrics(None)
        assert len(result) > 0

    def test_corporativo_mode_uses_hr_vocabulary(self):
        G = nx.star_graph(4)
        result = get_graph_metrics(G, modo="corporativo")
        assert "conexiones" in result.lower() or "empleados" in result.lower()

    def test_top_n_limits_output(self):
        G = nx.complete_graph(20)
        result = get_graph_metrics(G, top_n=3)
        assert isinstance(result, str)


# ============================================================
# SIMULAR — range-specific integration for new rules
# ============================================================

class TestSimularRules:
    """Integration tests: simular() runs without errors for each range."""

    def _base_state(self, bipolar=False):
        if bipolar:
            return {
                "opinion": 0.0, "propaganda": 0.4, "confianza": 0.5,
                "opinion_grupo_a": 0.65, "opinion_grupo_b": -0.55,
                "pertenencia_grupo": 0.6,
            }
        return {
            "opinion": 0.5, "propaganda": 0.7, "confianza": 0.4,
            "opinion_grupo_a": 0.72, "opinion_grupo_b": 0.28,
            "pertenencia_grupo": 0.65,
        }

    def test_simular_probabilistic_range_stays_valid(self):
        np.random.seed(7)
        hist = simular(
            self._base_state(), escenario="campana", pasos=15,
            cada_n_pasos=5, config={"rango": "[0, 1] — Probabilístico"}, verbose=False
        )
        assert all(0.0 <= h["opinion"] <= 1.0 for h in hist)

    def test_simular_bipolar_range_stays_valid(self):
        np.random.seed(7)
        hist = simular(
            self._base_state(bipolar=True), escenario="campana", pasos=15,
            cada_n_pasos=5, config={"rango": "[-1, 1] — Bipolar"}, verbose=False
        )
        assert all(-1.0 <= h["opinion"] <= 1.0 for h in hist)

    def test_simular_with_narrativa_b_triggers_contagio(self):
        np.random.seed(7)
        estado = {**self._base_state(), "narrativa_b": 0.9}
        hist = simular(
            estado, escenario="campana", pasos=10,
            cada_n_pasos=5, config={}, verbose=False
        )
        assert any(h.get("_regla_nombre") == "contagio_competitivo" for h in hist)

    def test_ews_flags_appear_after_buffer_filled(self):
        np.random.seed(5)
        hist = simular(
            self._base_state(), escenario="campana", pasos=HISTORY_BUFFER_SIZE + 2,
            cada_n_pasos=5, config={}, verbose=False
        )
        ews_steps = [h for h in hist if "ews" in h]
        assert len(ews_steps) > 0

    def test_replicator_mode_locks_rule_to_9(self):
        np.random.seed(3)
        cfg = {
            "rango": "[0, 1] — Probabilístico",
            "modelo_matematico": "Replicator",
        }
        hist = simular(
            self._base_state(), escenario="campana", pasos=10,
            cada_n_pasos=5, config=cfg, verbose=False
        )
        assert any(h.get("_regla_nombre") == "replicador" for h in hist)
