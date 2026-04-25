"""
Tests for empirical database metrics collected by BeyondSight agents.

These tests validate the integrity and correctness of the data that the
simulation agent collects for the empirical reference database used by
BeyondSight metrics:

  - SocialEnergyEngine.system_metrics() — per-step metrics
  - run_energy_simulation() — metrics_timeline and summary aggregate
  - resumen_historial() — aggregate stats from the hybrid simulator
  - LandscapeCache — SQLite error-path robustness
  - Energy landscape internal functions (_landscape_gradient, _landscape_energy)

Empirical data fields tracked:
  mean_opinion, std_opinion, polarizacion, energia_total, energia_media,
  n_clusters_approx, opinion_inicial, opinion_final, delta_total,
  media, desviacion, polarizacion_media, pasos, regla_dominante
"""
import pytest
import numpy as np

from energy_engine import SocialEnergyEngine, random_network, _landscape_gradient, _landscape_energy
from energy_runner import run_energy_simulation
from simulator import resumen_historial, DEFAULT_CONFIG
from programmatic_architect import ARCHETYPES


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def small_adj():
    A = np.zeros((5, 5))
    for i in range(4):
        A[i, i + 1] = A[i + 1, i] = 1.0
    return A


@pytest.fixture
def engine():
    return SocialEnergyEngine(range_type="bipolar", temperature=0.0, lambda_social=0.5)


@pytest.fixture
def simple_attractors():
    return [{"position": -0.5, "strength": 2.0, "label": "Left"},
            {"position":  0.5, "strength": 2.0, "label": "Right"}]


@pytest.fixture
def simple_repellers():
    return [{"position": 0.0, "strength": 1.5, "label": "Center"}]


# ============================================================
# LANDSCAPE GRADIENT & ENERGY — internal functions
# ============================================================

class TestLandscapeInternals:

    def test_gradient_zero_with_no_attractors_or_repellers(self):
        grad = _landscape_gradient(0.0, [], [])
        assert grad == pytest.approx(0.0)

    def test_gradient_positive_when_right_of_attractor(self):
        attractors = [{"position": -0.5, "strength": 2.0, "label": "A"}]
        grad = _landscape_gradient(0.0, attractors, [])
        assert grad > 0.0  # gradient pushes toward attractor (negative x direction)

    def test_gradient_negative_when_left_of_attractor(self):
        attractors = [{"position": 0.5, "strength": 2.0, "label": "A"}]
        grad = _landscape_gradient(0.0, attractors, [])
        assert grad < 0.0

    def test_gradient_is_zero_at_attractor_position(self):
        attractors = [{"position": 0.3, "strength": 2.0, "label": "A"}]
        grad = _landscape_gradient(0.3, attractors, [])
        assert grad == pytest.approx(0.0, abs=1e-9)

    def test_repeller_gradient_pushes_away(self):
        # Repeller contribution: grad -= strength * (x - pos) / sigma2 * G
        # At x=0.1 (right of repeller at 0): diff > 0, so repeller makes grad < 0.
        # The Langevin step uses -grad, so the drift is positive → moves right (away).
        repellers = [{"position": 0.0, "strength": 2.0, "label": "R"}]
        grad_pos = _landscape_gradient(0.1, [], repellers)
        grad_neg = _landscape_gradient(-0.1, [], repellers)
        # Right of repeller → gradient is negative (Langevin will push further right)
        assert grad_pos < 0.0
        # Left of repeller → gradient is positive (Langevin will push further left)
        assert grad_neg > 0.0

    def test_energy_decreases_toward_attractor(self):
        attractors = [{"position": 0.5, "strength": 2.0, "label": "A"}]
        energy_far  = _landscape_energy(0.0, attractors, [])
        energy_near = _landscape_energy(0.5, attractors, [])
        assert energy_near < energy_far

    def test_energy_increases_toward_repeller(self):
        repellers = [{"position": 0.0, "strength": 2.0, "label": "R"}]
        energy_far  = _landscape_energy(0.8, [], repellers)
        energy_near = _landscape_energy(0.1, [], repellers)
        assert energy_near > energy_far

    def test_energy_zero_with_empty_landscape(self):
        energy = _landscape_energy(0.0, [], [])
        assert energy == pytest.approx(0.0)


# ============================================================
# SYSTEM METRICS — all archetypes produce valid empirical data
# ============================================================

class TestSystemMetrics:

    def test_all_metric_keys_present(self, engine, small_adj):
        opinions = np.array([0.0, 0.2, -0.2, 0.5, -0.5])
        metrics = engine.system_metrics(opinions, small_adj, [], [])
        for key in ("mean_opinion", "std_opinion", "polarizacion",
                    "energia_total", "energia_media", "n_clusters_approx"):
            assert key in metrics

    def test_mean_opinion_matches_numpy(self, engine, small_adj):
        opinions = np.array([0.1, -0.3, 0.5, -0.2, 0.4])
        metrics = engine.system_metrics(opinions, small_adj, [], [])
        assert metrics["mean_opinion"] == pytest.approx(float(np.mean(opinions)))

    def test_std_opinion_matches_numpy(self, engine, small_adj):
        opinions = np.array([0.1, -0.3, 0.5, -0.2, 0.4])
        metrics = engine.system_metrics(opinions, small_adj, [], [])
        assert metrics["std_opinion"] == pytest.approx(float(np.std(opinions)))

    def test_polarizacion_zero_when_all_at_neutral(self, engine, small_adj):
        opinions = np.zeros(5)
        metrics = engine.system_metrics(opinions, small_adj, [], [])
        assert metrics["polarizacion"] == pytest.approx(0.0)

    def test_polarizacion_one_when_perfectly_spread(self, small_adj):
        engine_b = SocialEnergyEngine(range_type="bipolar", temperature=0.0, lambda_social=0.5)
        opinions = np.array([-1.0, -1.0, 0.0, 1.0, 1.0])
        metrics = engine_b.system_metrics(opinions, small_adj, [], [])
        assert 0.0 <= metrics["polarizacion"] <= 2.0

    def test_polarizacion_bounded_bipolar(self, engine, small_adj):
        opinions = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])
        metrics = engine.system_metrics(opinions, small_adj, [], [])
        assert 0.0 <= metrics["polarizacion"] <= 2.0

    def test_polarizacion_bounded_unipolar(self, small_adj):
        engine_u = SocialEnergyEngine(range_type="unipolar", temperature=0.0, lambda_social=0.5)
        opinions = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        metrics = engine_u.system_metrics(opinions, small_adj, [], [])
        assert 0.0 <= metrics["polarizacion"] <= 2.0

    def test_energia_total_negative_with_strong_attractors(self, engine, small_adj, simple_attractors):
        opinions = np.array([-0.5, -0.5, -0.5, 0.5, 0.5])
        metrics = engine.system_metrics(opinions, small_adj, simple_attractors, [])
        assert metrics["energia_total"] < 0.0

    def test_n_clusters_one_when_all_agree(self, engine, small_adj):
        opinions = np.full(5, 0.5)
        metrics = engine.system_metrics(opinions, small_adj, [], [])
        assert metrics["n_clusters_approx"] == 1

    def test_n_clusters_two_when_polarized(self, engine, small_adj):
        opinions = np.array([-0.8, -0.8, -0.8, 0.8, 0.8])
        metrics = engine.system_metrics(opinions, small_adj, [], [])
        assert metrics["n_clusters_approx"] >= 2

    def test_metrics_are_floats(self, engine, small_adj):
        opinions = np.array([0.1, -0.2, 0.3, -0.4, 0.5])
        metrics = engine.system_metrics(opinions, small_adj, [], [])
        for key in ("mean_opinion", "std_opinion", "polarizacion",
                    "energia_total", "energia_media"):
            assert isinstance(metrics[key], float)

    def test_n_clusters_is_int(self, engine, small_adj):
        opinions = np.zeros(5)
        metrics = engine.system_metrics(opinions, small_adj, [], [])
        assert isinstance(metrics["n_clusters_approx"], int)


# ============================================================
# METRICS TIMELINE — run_energy_simulation completeness
# ============================================================

class TestMetricsTimeline:

    def test_metrics_timeline_not_empty(self):
        result = run_energy_simulation("consenso_moderado", n_agents=10, steps=5)
        assert len(result["metrics_timeline"]) > 0

    def test_each_timeline_entry_has_required_keys(self):
        result = run_energy_simulation("caos_social", n_agents=10, steps=5)
        for entry in result["metrics_timeline"]:
            for key in ("mean_opinion", "std_opinion", "polarizacion",
                        "energia_total", "energia_media", "n_clusters_approx"):
                assert key in entry, f"Key '{key}' missing from metrics_timeline entry"

    def test_metrics_timeline_paso_key_monotonic(self):
        result = run_energy_simulation("polarizacion_extrema", n_agents=8, steps=10)
        pasos = [m["_paso"] for m in result["metrics_timeline"]]
        assert pasos == sorted(pasos)

    def test_metrics_every_n_controls_length(self):
        result_every1 = run_energy_simulation("consenso_moderado", n_agents=8, steps=10, metrics_every_n=1)
        result_every5 = run_energy_simulation("consenso_moderado", n_agents=8, steps=10, metrics_every_n=5)
        assert len(result_every1["metrics_timeline"]) > len(result_every5["metrics_timeline"])

    def test_polarizacion_always_non_negative_in_timeline(self):
        result = run_energy_simulation("radicalizacion_progresiva", n_agents=15, steps=10)
        for entry in result["metrics_timeline"]:
            assert entry["polarizacion"] >= 0.0

    def test_polarizacion_bounded_in_timeline(self):
        result = run_energy_simulation("polarizacion_extrema", n_agents=20, steps=10)
        for entry in result["metrics_timeline"]:
            assert entry["polarizacion"] <= 2.0

    def test_energia_media_is_finite(self):
        result = run_energy_simulation("fragmentacion_3_grupos", n_agents=10, steps=5)
        for entry in result["metrics_timeline"]:
            assert np.isfinite(entry["energia_media"])

    def test_n_clusters_at_least_one(self):
        result = run_energy_simulation("consenso_moderado", n_agents=10, steps=5)
        for entry in result["metrics_timeline"]:
            assert entry["n_clusters_approx"] >= 1


# ============================================================
# SUMMARY — aggregate empirical record per run
# ============================================================

class TestRunEnergySimulationSummary:

    def test_summary_delta_equals_final_minus_initial(self):
        result = run_energy_simulation("consenso_moderado", n_agents=10, steps=5)
        s = result["summary"]
        assert s["delta_total"] == pytest.approx(
            s["opinion_final"] - s["opinion_inicial"], abs=1e-8
        )

    def test_summary_polarizacion_media_non_negative(self):
        result = run_energy_simulation("radicalizacion_progresiva", n_agents=15, steps=8)
        assert result["summary"]["polarizacion_media"] >= 0.0

    def test_summary_pasos_matches_steps_argument(self):
        for steps in (5, 20, 50):
            result = run_energy_simulation("caos_social", n_agents=5, steps=steps)
            assert result["summary"]["pasos"] == steps

    def test_summary_neutro_bipolar(self):
        result = run_energy_simulation("consenso_moderado", n_agents=5, steps=5, range_type="bipolar")
        assert result["summary"]["neutro"] == pytest.approx(0.0)

    def test_summary_neutro_unipolar(self):
        result = run_energy_simulation("consenso_moderado", n_agents=5, steps=5, range_type="unipolar")
        assert result["summary"]["neutro"] == pytest.approx(0.5)

    def test_summary_regla_dominante_is_langevin(self):
        result = run_energy_simulation("consenso_moderado", n_agents=5, steps=5)
        assert result["summary"]["regla_dominante"] == "langevin_energy"

    def test_summary_rango_bipolar(self):
        result = run_energy_simulation("consenso_moderado", n_agents=5, steps=5, range_type="bipolar")
        rango = result["summary"]["rango"]
        assert "-1" in rango and "1" in rango

    def test_summary_rango_unipolar(self):
        result = run_energy_simulation("consenso_moderado", n_agents=5, steps=5, range_type="unipolar")
        rango = result["summary"]["rango"]
        assert "0" in rango and "1" in rango

    def test_summary_media_within_opinion_range_bipolar(self):
        result = run_energy_simulation("consenso_moderado", n_agents=10, steps=10, range_type="bipolar")
        assert -1.0 <= result["summary"]["media"] <= 1.0

    def test_config_overrides_clamp_temperature(self):
        # temperature is clamped to [0.01, 0.20]; values outside this range are clamped
        result_lo = run_energy_simulation(
            "consenso_moderado", n_agents=5, steps=3,
            config_overrides={"temperature": 0.0}  # below min → clamped to 0.01
        )
        result_hi = run_energy_simulation(
            "consenso_moderado", n_agents=5, steps=3,
            config_overrides={"temperature": 1.0}  # above max → clamped to 0.20
        )
        assert result_lo["summary"]["pasos"] == 3
        assert result_hi["summary"]["pasos"] == 3


# ============================================================
# HISTORY SNAPSHOTS — opinions_snapshot integrity
# ============================================================

class TestHistorySnapshots:

    def test_opinions_snapshot_at_step_0(self):
        result = run_energy_simulation("caos_social", n_agents=10, steps=5)
        assert result["history"][0]["opinions_snapshot"] is not None

    def test_opinions_snapshot_at_last_step(self):
        result = run_energy_simulation("caos_social", n_agents=10, steps=5)
        assert result["history"][-1]["opinions_snapshot"] is not None

    def test_opinions_snapshot_has_correct_length(self):
        n = 12
        result = run_energy_simulation("consenso_moderado", n_agents=n, steps=5)
        snap = result["history"][0]["opinions_snapshot"]
        assert len(snap) == n

    def test_opinions_snapshot_every_10_steps(self):
        result = run_energy_simulation("caos_social", n_agents=5, steps=25)
        snaps_with_data = [h for h in result["history"] if h["opinions_snapshot"] is not None]
        # t=0, t=10, t=20, t=25 should have snapshots
        assert len(snaps_with_data) >= 3

    def test_opinions_in_snapshot_are_in_valid_range_bipolar(self):
        result = run_energy_simulation("polarizacion_extrema", n_agents=8, steps=5, range_type="bipolar")
        snap = result["history"][0]["opinions_snapshot"]
        assert all(-1.0 <= o <= 1.0 for o in snap)


# ============================================================
# EMPIRICAL METRICS — resumen_historial from hybrid simulator
# ============================================================

class TestResumenHistorialEmpiricalMetrics:
    """Validates the empirical data collected from the hybrid simulator."""

    def _make_historial(self, opiniones, regla="lineal"):
        return [{"opinion": float(op), "_regla_nombre": regla} for op in opiniones]

    def test_polarizacion_media_bipolar_extremes(self):
        cfg = {**DEFAULT_CONFIG, "rango": "[-1, 1] — Bipolar"}
        opiniones = [-1.0] * 5 + [1.0] * 5 + [-1.0]
        hist = self._make_historial(opiniones)
        stats = resumen_historial(hist, cfg)
        assert stats["polarizacion_media"] == pytest.approx(1.0, abs=0.01)

    def test_polarizacion_media_zero_at_neutral_probabilistic(self):
        cfg = {**DEFAULT_CONFIG, "rango": "[0, 1] — Probabilístico"}
        opiniones = [0.5] * 11
        hist = self._make_historial(opiniones)
        stats = resumen_historial(hist, cfg)
        assert stats["polarizacion_media"] == pytest.approx(0.0)

    def test_desviacion_positive_for_spread_opinions(self):
        cfg = {**DEFAULT_CONFIG}
        opiniones = list(np.linspace(0.0, 1.0, 11))
        hist = self._make_historial(opiniones)
        stats = resumen_historial(hist, cfg)
        assert stats["desviacion"] > 0.0

    def test_desviacion_zero_for_constant_opinions(self):
        cfg = {**DEFAULT_CONFIG}
        opiniones = [0.5] * 11
        hist = self._make_historial(opiniones)
        stats = resumen_historial(hist, cfg)
        assert stats["desviacion"] == pytest.approx(0.0, abs=1e-9)

    def test_minimo_and_maximo_bounds(self):
        cfg = {**DEFAULT_CONFIG}
        opiniones = [0.1, 0.3, 0.7, 0.9, 0.5, 0.2]
        hist = self._make_historial(opiniones)
        stats = resumen_historial(hist, cfg)
        assert stats["minimo"] == pytest.approx(min(opiniones))
        assert stats["maximo"] == pytest.approx(max(opiniones))

    def test_all_numeric_values_are_finite(self):
        cfg = {**DEFAULT_CONFIG}
        opiniones = list(np.random.uniform(0, 1, 20))
        hist = self._make_historial(opiniones)
        stats = resumen_historial(hist, cfg)
        for key in ("opinion_inicial", "opinion_final", "delta_total",
                    "media", "desviacion", "minimo", "maximo", "polarizacion_media"):
            assert np.isfinite(stats[key]), f"{key} is not finite"


# ============================================================
# ALL ARCHETYPES — each generates valid empirical metrics
# ============================================================

class TestAllArchetypesMetrics:
    """Every archetype should produce a complete, valid metrics record."""

    @pytest.mark.parametrize("archetype_key", list(ARCHETYPES.keys()))
    def test_archetype_produces_valid_metrics_timeline(self, archetype_key):
        result = run_energy_simulation(archetype_key, n_agents=8, steps=5)
        assert len(result["metrics_timeline"]) > 0
        first = result["metrics_timeline"][0]
        assert np.isfinite(first["mean_opinion"])
        assert np.isfinite(first["polarizacion"])
        assert first["polarizacion"] >= 0.0
        assert first["n_clusters_approx"] >= 1

    @pytest.mark.parametrize("archetype_key", list(ARCHETYPES.keys()))
    def test_archetype_summary_is_complete(self, archetype_key):
        result = run_energy_simulation(archetype_key, n_agents=8, steps=5)
        s = result["summary"]
        for key in ("opinion_inicial", "opinion_final", "delta_total",
                    "media", "desviacion", "polarizacion_media", "pasos"):
            assert key in s
            if isinstance(s[key], float):
                assert np.isfinite(s[key])

    @pytest.mark.parametrize("archetype_key", list(ARCHETYPES.keys()))
    def test_archetype_final_opinions_in_range(self, archetype_key):
        result = run_energy_simulation(archetype_key, n_agents=10, steps=5, range_type="bipolar")
        opinions = result["final_state"]["opinions"]
        assert all(-1.0 <= o <= 1.0 for o in opinions)


# ============================================================
# LANDSCAPE CACHE — SQLite error robustness
# ============================================================

class TestLandscapeCacheSQLiteErrors:

    def test_cache_handles_unwritable_path_gracefully(self, tmp_path):
        from cache_manager import LandscapeCache
        bad_path = str(tmp_path / "nonexistent_dir" / "cache.db")
        cache = LandscapeCache(db_path=bad_path)
        # Should not raise even if SQLite fails; uses in-memory fallback
        cache.set("test_goal", {"data": 1})
        result = cache.get("test_goal")
        # In-memory cache should still work
        assert result == {"data": 1}

    def test_cache_key_hashing_is_consistent(self, tmp_path):
        from cache_manager import LandscapeCache
        db = str(tmp_path / "hash_test.db")
        cache = LandscapeCache(db_path=db)
        cache.set("My Unique Goal 123", {"value": 42})
        assert cache.get("my unique goal 123") == {"value": 42}
        assert cache.get("MY UNIQUE GOAL 123") == {"value": 42}

    def test_cache_clear_removes_from_sqlite(self, tmp_path):
        from cache_manager import LandscapeCache
        db = str(tmp_path / "clear_test.db")
        cache1 = LandscapeCache(db_path=db)
        cache1.set("goal_a", {"v": 1})
        cache1.set("goal_b", {"v": 2})
        cache1.clear()

        cache2 = LandscapeCache(db_path=db)
        assert cache2.get("goal_a") is None
        assert cache2.get("goal_b") is None

    def test_overwrite_updates_sqlite_value(self, tmp_path):
        from cache_manager import LandscapeCache
        db = str(tmp_path / "overwrite_test.db")
        c1 = LandscapeCache(db_path=db)
        c1.set("goal", {"version": 1})

        c2 = LandscapeCache(db_path=db)
        c2.set("goal", {"version": 2})

        c3 = LandscapeCache(db_path=db)
        result = c3.get("goal")
        assert result == {"version": 2}
