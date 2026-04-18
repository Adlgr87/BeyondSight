import pytest
import requests.exceptions
from unittest.mock import patch, MagicMock
from simulator import llamar_llm, simular, DEFAULT_CONFIG

def test_llm_selector_fallback():
    """
    Test that when the LLM provider fails (connection error), the system falls
    back to the heuristic selector and returns a valid rule dictionary.
    """
    estado = {"opinion": 0.5, "propaganda": 0.1}
    cfg = {**DEFAULT_CONFIG, "proveedor": "openai", "api_key": "fake"}

    with patch("requests.post") as mock_post:
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection Error")

        resultado = llamar_llm(estado, "campana", [estado], cfg)

        assert "regla" in resultado
        assert "razon" in resultado
        assert isinstance(resultado["regla"], int)

def test_llm_selector_success():
    """
    Test a successful LLM rule selection mock.
    """
    estado = {"opinion": 0.5, "propaganda": 0.8}
    cfg = {**DEFAULT_CONFIG, "proveedor": "groq", "api_key": "fake"}

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "choices": [{
            "message": {
                "content": '{"regla": 1, "params": {}, "razon": "High propaganda detected"}'
            }
        }]
    }

    with patch("requests.post", return_value=mock_response):
        resultado = llamar_llm(estado, "campana", [estado], cfg)

        assert resultado["regla"] == 1
        assert "High propaganda" in resultado["razon"]

def test_simulation_integration():
    """
    Test that the simular function runs end-to-end with the heuristic selector.
    """
    estado_inicial = {"opinion": 0.0, "propaganda": 0.5}
    config = {"proveedor": "heurístico", "rango": "[-1, 1] — Bipolar"}

    historial = simular(estado_inicial, pasos=10, cada_n_pasos=2, config=config)

    assert len(historial) == 11  # t=0 + 10 steps
    assert "_regla_nombre" in historial[1]
    assert all("opinion" in h for h in historial)
