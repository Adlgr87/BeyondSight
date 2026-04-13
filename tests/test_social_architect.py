import pytest
from social_architect import evaluar_resultado, parse_llm_strategy

def test_evaluar_resultado_consenso():
    # Simulate a network that successfully reached consensus around 0.5 (Neutrality/Agreement)
    objetivo = "consenso"
    historial = [
        {"opinion": 0.5, "pertenencia_grupo": 0.5, "_paso": 0},
        {"opinion": 0.5, "pertenencia_grupo": 0.5, "_paso": 1},
        {"opinion": 0.5, "pertenencia_grupo": 0.5, "_paso": 2},
    ]
    
    score, feedback = evaluar_resultado(historial, objetivo)
    
    # Score should be high for consensus
    assert score >= 80
    assert "Éxito" in feedback or "converg" in feedback.lower()

def test_evaluar_resultado_falla_polarizacion():
    # Simulate a network that should have reached consensus but remained extremely partisan
    objetivo = "despolarizar"
    # Using range [0, 1], so 0.9 and 0.1 are polarized. Average is 0.5 but variance is high.
    # However, social_architect evaluation uses polarizacion_media from stats.
    # To make it fail, we need high polarizacion.
    historial = [
        {"opinion": 0.9, "pertenencia_grupo": 0.5, "_paso": 0},
        {"opinion": 0.1, "pertenencia_grupo": 0.5, "_paso": 1},
    ]
    
    score, feedback = evaluar_resultado(historial, objetivo)
    
    # Polarizacion might be high, so score should be low
    assert score < 60
    assert "Ajuste insuficiente" in feedback

def test_parsear_estrategia_valida():
    # Valid strategy payload from LLM
    json_text = '''
    ```json
    {
      "interventions": [
        {"time_start": 0, "time_end": 5, "model_name": "lineal", "parameters": {}, "fase_rationale": "Init"}
      ]
    }
    ```
    '''
    resultado = parse_llm_strategy(json_text)
    assert "interventions" in resultado
    assert len(resultado["interventions"]) == 1
    assert resultado["interventions"][0]["model_name"] == "lineal"
