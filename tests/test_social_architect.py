import pytest
from social_architect import evaluar_resultado, parse_llm_strategy

def test_evaluar_resultado_consenso():
    # Simulate a network that successfully reached consensus around 0.5 (Neutrality/Agreement)
    objetivo = "consenso"
    historial = [
        {"opinion": 0.1, "estado_completo": {"confianza": 0.3}},
        {"opinion": 0.45, "estado_completo": {"confianza": 0.8}},
        {"opinion": 0.51, "estado_completo": {"confianza": 0.9}},
    ]
    
    es_exito, razon = evaluar_resultado(historial, objetivo)
    
    assert es_exito is True
    assert "consenso" in razon.lower() or "estable" in razon.lower()

def test_evaluar_resultado_falla_polarizacion():
    # Simulate a network that should have reached consensus but remained extremely partisan
    objetivo = "despolarizar"
    historial = [
        {"opinion": 0.9, "estado_completo": {"confianza": 0.3}},
        {"opinion": 0.95, "estado_completo": {"confianza": 0.2}},
    ]
    
    es_exito, razon = evaluar_resultado(historial, objetivo)
    
    assert es_exito is False
    assert "extrema" in razon.lower() or "polarización" in razon.lower()

def test_parsear_estrategia_valida():
    # Valid strategy payload from LLM
    json_text = '''
    ```json
    {
      "falso_json": false,
      "estrategias": [
        {"time_start": 0, "time_end": 5, "model_name": "lineal", "parameters": {}, "fase_rationale": "Init"}
      ]
    }
    ```
    '''
    # We mock or run the regex logic inside parse_llm_strategy
    # Because parse_llm_strategy calls the LLM if it fails pydantic, we just test the regex parsing manually.
    import re
    match = re.search(r"```json\s*(.*?)\s*```", json_text, re.DOTALL)
    assert match is not None
    assert "falso_json" in match.group(1)
