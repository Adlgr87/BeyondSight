import unittest

import numpy as np

from simulator import calcular_efecto_grupos, resumen_historial, simular


class SimulatorTests(unittest.TestCase):
    def setUp(self):
        np.random.seed(42)
        self.estado_base = {
            "opinion": 0.5,
            "propaganda": 0.7,
            "confianza": 0.4,
            "tension": 0.3,
            "opinion_grupo_a": 0.72,
            "opinion_grupo_b": 0.28,
            "pertenencia_grupo": 0.65,
        }

    def test_simular_devuelve_historial_valido(self):
        historial = simular(
            self.estado_base,
            escenario="campana",
            pasos=20,
            cada_n_pasos=5,
            usar_llm_real=False,
            verbose=False,
        )

        self.assertEqual(len(historial), 21)
        self.assertEqual(historial[0]["opinion"], self.estado_base["opinion"])
        self.assertTrue(all(0.0 <= h["opinion"] <= 1.0 for h in historial))
        self.assertTrue(all("_regla_nombre" in h for h in historial[1:]))

    def test_resumen_historial_consistente(self):
        historial = simular(
            self.estado_base,
            escenario="campana",
            pasos=10,
            cada_n_pasos=2,
            usar_llm_real=False,
            verbose=False,
        )
        stats = resumen_historial(historial)

        self.assertEqual(stats["pasos"], 10)
        self.assertGreaterEqual(stats["maximo"], stats["minimo"])
        self.assertAlmostEqual(
            stats["delta_total"],
            stats["opinion_final"] - stats["opinion_inicial"],
            places=10,
        )

    def test_efecto_grupos_empuja_hacia_referencia_social(self):
        estado = {
            "opinion": 0.2,
            "opinion_grupo_a": 0.9,
            "opinion_grupo_b": 0.1,
            "pertenencia_grupo": 0.8,
        }
        cfg = {"efecto_vecinos_peso": 0.05}
        efecto = calcular_efecto_grupos(estado, cfg)
        self.assertGreater(efecto, 0.0)


if __name__ == "__main__":
    unittest.main()
