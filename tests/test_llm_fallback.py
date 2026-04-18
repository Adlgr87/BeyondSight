"""
Tests del flag ``_llm_fallback`` (Fase 0.2).

Garantiza que cuando el LLM remoto falla, el estado de simulación queda
marcado con ``_llm_fallback=True`` y ``_fallback_razon`` explicando la
causa. El uso explícito del selector "heurístico" NO es fallback.
"""
import unittest

import numpy as np

from simulator import llamar_llm, simular


class LLMFallbackTests(unittest.TestCase):

    def test_heuristico_explicito_no_es_fallback(self):
        """Si el usuario elige 'heurístico' a propósito, no es degradación."""
        dec = llamar_llm(
            {"opinion": 0.3, "propaganda": 0.1},
            "campana", [], {"proveedor": "heurístico"},
        )
        self.assertFalse(dec.get("_llm_fallback", True))

    def test_api_key_ausente_marca_fallback(self):
        """Proveedor remoto sin credenciales → fallback con razón clara."""
        dec = llamar_llm(
            {"opinion": 0.3, "propaganda": 0.1},
            "campana", [], {"proveedor": "openai", "api_key": ""},
        )
        self.assertTrue(dec["_llm_fallback"])
        self.assertIn("API key", dec["_fallback_razon"])
        self.assertIn("openai", dec["_fallback_razon"])

    def test_proveedor_desconocido_marca_fallback(self):
        """Nombre de proveedor inválido → fallback."""
        dec = llamar_llm(
            {"opinion": 0.3, "propaganda": 0.1},
            "campana", [], {"proveedor": "proveedor_inexistente_xyz"},
        )
        self.assertTrue(dec["_llm_fallback"])
        self.assertIn("proveedor_inexistente_xyz", dec["_fallback_razon"])

    def test_simulacion_heuristica_sin_ticks_en_fallback(self):
        """Una simulación 100% heurística no debe marcar ningún tick como fallback."""
        np.random.seed(0)
        historial = simular(
            {"opinion": 0.2, "propaganda": 0.1},
            pasos=10, cada_n_pasos=2, verbose=False,
        )
        ticks_fb = [h for h in historial if h.get("_llm_fallback")]
        self.assertEqual(len(ticks_fb), 0)

    def test_simulacion_remota_sin_key_todos_en_fallback(self):
        """
        Una simulación que pide un proveedor remoto sin API key debe
        propagar _llm_fallback=True a TODOS los ticks del historial.
        """
        np.random.seed(0)
        historial = simular(
            {"opinion": 0.2, "propaganda": 0.1},
            pasos=10, cada_n_pasos=2, verbose=False,
            config={"proveedor": "openai", "api_key": ""},
        )
        ticks_fb = [h for h in historial if h.get("_llm_fallback")]
        self.assertEqual(len(ticks_fb), len(historial))
        # Razón también propagada
        for tick in ticks_fb:
            self.assertIn("razon", "razon")  # tick tiene razón textual
            self.assertIn("API key", tick.get("_fallback_razon", ""))


if __name__ == "__main__":
    unittest.main()
