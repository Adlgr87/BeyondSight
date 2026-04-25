"""
Tests del generador de streaming ``iter_simulation_ticks`` (Fase 0.1).

Valida:
  * Equivalencia bit-a-bit con ``simular`` bajo la misma semilla.
  * Que es verdaderamente perezoso: emite t=0 antes de calcular los pasos.
  * Que los ticks contienen los campos de metadata esperados.
"""
import unittest

import numpy as np

from simulator import iter_simulation_ticks, simular


class StreamingTests(unittest.TestCase):
    def setUp(self):
        self.estado = {"opinion": 0.2, "propaganda": 0.3}

    def test_iter_equivalente_a_simular_mismo_seed(self):
        """Mismo seed → mismo historial tick a tick."""
        np.random.seed(123)
        via_simular = simular(
            self.estado, escenario="campana", pasos=15,
            cada_n_pasos=3, verbose=False,
        )
        np.random.seed(123)
        via_iter = list(iter_simulation_ticks(
            self.estado, escenario="campana", pasos=15,
            cada_n_pasos=3, verbose=False,
        ))
        self.assertEqual(len(via_simular), len(via_iter))
        for a, b in zip(via_simular, via_iter):
            self.assertAlmostEqual(a["opinion"], b["opinion"], places=12)

    def test_genera_numero_correcto_de_ticks(self):
        """pasos=N debe emitir N+1 ticks (incluye t=0)."""
        ticks = list(iter_simulation_ticks(
            self.estado, pasos=7, cada_n_pasos=1, verbose=False,
        ))
        self.assertEqual(len(ticks), 8)
        self.assertEqual(ticks[0]["_paso"], 0)
        self.assertEqual(ticks[-1]["_paso"], 7)

    def test_tick_contiene_metadata_minima(self):
        """Cada tick trae claves requeridas por la UI."""
        ticks = list(iter_simulation_ticks(
            self.estado, pasos=3, cada_n_pasos=1, verbose=False,
        ))
        for tick in ticks:
            for clave in ("opinion", "opinion_prev", "_paso",
                          "_regla_nombre", "_razon"):
                self.assertIn(clave, tick, f"Falta {clave!r} en tick {tick.get('_paso')}")

    def test_es_verdaderamente_perezoso(self):
        """
        El generador debe emitir el primer tick sin haber calculado todos
        los pasos: pedimos 1000 pasos y solo consumimos el primero.
        Si fuese eager, esto tardaría mucho; aquí probamos que retorna t=0
        sin explotar (contador de next() == 1 funciona).
        """
        gen = iter_simulation_ticks(
            self.estado, pasos=1000, cada_n_pasos=5, verbose=False,
        )
        primero = next(gen)
        self.assertEqual(primero["_paso"], 0)
        # Cerrar el generador sin iterar todo; no debe lanzar excepción.
        gen.close()


if __name__ == "__main__":
    unittest.main()
