import unittest

from realtime_bridge import build_visualization_state
from simulator import iter_simulation_ticks


class RealtimeBridgeTests(unittest.TestCase):
    def test_build_visualization_state_structure(self):
        current = {
            "opinion": 0.6,
            "confianza": 0.4,
            "opinion_grupo_a": 0.8,
            "opinion_grupo_b": 0.2,
            "pertenencia_grupo": 0.65,
            "_regla_nombre": "polarizacion",
        }
        previous = {"opinion": 0.55}
        viz = build_visualization_state(
            state=current,
            tick=10,
            range_name="[0, 1] — Probabilístico",
            session_id="test-session",
            mode="macro",
            previous_state=previous,
            n_agents=20,
        )

        self.assertEqual(viz.session_id, "test-session")
        self.assertEqual(viz.mode, "macro")
        self.assertEqual(viz.metrics.tick, 10)
        self.assertEqual(len(viz.agents), 20)
        self.assertGreaterEqual(len(viz.edges), 1)
        self.assertGreaterEqual(viz.metrics.polarization, 0.0)
        self.assertLessEqual(viz.metrics.polarization, 1.0)
        self.assertTrue(viz.metrics.event_message)
        self.assertTrue(viz.metrics.narrative_message)

    def test_agent_visual_fields_ranges(self):
        current = {
            "opinion": -0.3,
            "confianza": 0.75,
            "opinion_grupo_a": 0.5,
            "opinion_grupo_b": -0.7,
            "pertenencia_grupo": 0.5,
            "_regla_nombre": "hk",
        }
        viz = build_visualization_state(
            state=current,
            tick=2,
            range_name="[-1, 1] — Bipolar",
            session_id="bipolar-session",
            mode="corporativo",
            previous_state=None,
            n_agents=15,
        )

        for a in viz.agents:
            self.assertGreaterEqual(a.x, 0.0)
            self.assertLessEqual(a.x, 1.0)
            self.assertGreaterEqual(a.y, 0.0)
            self.assertLessEqual(a.y, 1.0)
            self.assertGreaterEqual(a.influence, 0.0)
            self.assertLessEqual(a.influence, 1.0)
            self.assertGreaterEqual(a.volatility, 0.0)
            self.assertLessEqual(a.volatility, 1.0)
            self.assertGreaterEqual(a.mood_index, 0.0)
            self.assertLessEqual(a.mood_index, 1.0)
            self.assertTrue(a.color_hex.startswith("#"))
            self.assertEqual(len(a.color_hex), 7)

    def test_iter_simulation_ticks_emits_ordered_ticks(self):
        estado = {
            "opinion": 0.5,
            "propaganda": 0.7,
            "confianza": 0.4,
            "opinion_grupo_a": 0.72,
            "opinion_grupo_b": 0.28,
            "pertenencia_grupo": 0.65,
        }
        config = {"proveedor": "heurístico", "rango": "[0, 1] — Probabilístico"}
        ticks = list(
            iter_simulation_ticks(
                estado_inicial=estado,
                pasos=5,
                cada_n_pasos=2,
                config=config,
                verbose=False,
            )
        )

        self.assertEqual(len(ticks), 6)
        self.assertEqual(ticks[0]["_tick"], 0)
        self.assertEqual(ticks[-1]["_tick"], 5)
        self.assertTrue(all("_tick" in t for t in ticks))


if __name__ == "__main__":
    unittest.main()
