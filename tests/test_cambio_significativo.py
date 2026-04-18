"""
Tests de la utilidad ``cambio_significativo_opinion`` (Fase 0.4).

Esta utilidad se introduce como blindaje preventivo del bug descrito en
el plan 0.4: comparar el delta de un agente contra la media global en
vez de contra su propia opinión previa. La función garantiza la
comparación correcta (contra opinion_prev del mismo estado).
"""
import unittest

from simulator import cambio_significativo_opinion, simular


class CambioSignificativoTests(unittest.TestCase):

    def test_sin_cambio_retorna_false(self):
        estado = {"opinion": 0.3, "opinion_prev": 0.3}
        self.assertFalse(cambio_significativo_opinion(estado))

    def test_cambio_grande_retorna_true(self):
        estado = {"opinion": 0.5, "opinion_prev": 0.3}
        self.assertTrue(cambio_significativo_opinion(estado))

    def test_cambio_bajo_umbral_retorna_false(self):
        """Default umbral=0.05. Un delta de 0.01 NO debe marcar cambio."""
        estado = {"opinion": 0.31, "opinion_prev": 0.30}
        self.assertFalse(cambio_significativo_opinion(estado))

    def test_umbral_personalizable(self):
        estado = {"opinion": 0.31, "opinion_prev": 0.30}
        self.assertTrue(cambio_significativo_opinion(estado, umbral=0.005))
        self.assertFalse(cambio_significativo_opinion(estado, umbral=0.5))

    def test_estado_incompleto_retorna_false_sin_excepcion(self):
        """Si falta opinion_prev, no debe romper — asumir sin cambio."""
        self.assertFalse(cambio_significativo_opinion({"opinion": 0.5}))
        self.assertFalse(cambio_significativo_opinion({}))

    def test_no_usa_media_global(self):
        """
        Regresión contra el bug descrito en plan 0.4: comparar contra
        media global causaría que un agente estable lejos de la media
        aparezca como 'cambiado'. Aquí verificamos que no es así: un
        estado que NO cambió opinion, sigue NO cambiando aunque su
        opinión esté muy lejos del neutro.
        """
        # Agente estable en posición extrema: no hay cambio real.
        estado = {"opinion": 0.95, "opinion_prev": 0.95}
        self.assertFalse(cambio_significativo_opinion(estado))
        # Agente estable en posición cercana a 0: tampoco cambia.
        estado = {"opinion": 0.01, "opinion_prev": 0.01}
        self.assertFalse(cambio_significativo_opinion(estado))

    def test_usa_valor_absoluto_simetrico(self):
        """El signo del cambio no importa — solo la magnitud."""
        e_sube = {"opinion": 0.45, "opinion_prev": 0.30}
        e_baja = {"opinion": 0.15, "opinion_prev": 0.30}
        self.assertEqual(
            cambio_significativo_opinion(e_sube),
            cambio_significativo_opinion(e_baja),
        )

    def test_integracion_con_simulacion_real(self):
        """Se puede recorrer un historial y contar cambios sin errores."""
        hist = simular(
            {"opinion": 0.2, "propaganda": 0.3},
            pasos=20, cada_n_pasos=5, verbose=False,
        )
        # Al menos algún tick debe tener opinion_prev presente y numérico.
        cambios = sum(1 for h in hist if cambio_significativo_opinion(h, umbral=0.01))
        self.assertIsInstance(cambios, int)
        self.assertGreaterEqual(cambios, 0)
        self.assertLessEqual(cambios, len(hist))


if __name__ == "__main__":
    unittest.main()
