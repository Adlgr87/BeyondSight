import json
import logging
import os
from openai import OpenAI
from pydantic import ValidationError

from schemas import StrategyMatrix
from simulator import run_with_schedule, resumen_historial, DEFAULT_CONFIG

log = logging.getLogger("beyondsight")

def setup_client():
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    
    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")
        base_url = "https://api.groq.com/openai/v1"
    if not api_key:
        api_key = os.getenv("OPENROUTER_API_KEY")
        base_url = "https://openrouter.ai/api/v1"
        
    if not api_key:
        return OpenAI() # Uses default env variables from user
    return OpenAI(api_key=api_key, base_url=base_url)

def evaluar_resultado(historial, objetivo_usuario, config):
    """
    Calcula un score (0 a 100) y genera texto de feedback para el LLM.
    """
    stats = resumen_historial(historial, config)
    polarizacion = stats["polarizacion_media"]
    delta = stats["delta_total"]
    
    estado_final = (
        f"Opinión Inicial={stats['opinion_inicial']:.3f}, "
        f"Opinión Final={stats['opinion_final']:.3f}, Delta={delta:+.3f}, "
        f"Polarización Media={polarizacion:.3f}, Varianza={stats['desviacion']:.3f}. "
    )
    
    obj_lower = objetivo_usuario.lower()
    if any(palabra in obj_lower for palabra in ["consenso", "despolarizar", "apaciguar"]):
        score = max(0, min(100, 100 - (polarizacion * 100 * 2)))
        if stats['desviacion'] < 0.15:
            score += 20
    elif any(palabra in obj_lower for palabra in ["polariza", "dividir"]):
        score = min(100, polarizacion * 100 * 2)
    else:
        score = 80 if abs(delta) > 0.05 else 40
        
    score = min(100, max(0, score))
    
    feedback = estado_final
    if score >= 90:
        feedback += "¡Éxito! La red convergió según el objetivo buscado."
    else:
        feedback += f"El resultado fue {score:.1f}%. Ajuste insuficiente. "
        if polarizacion > 0.2:
            feedback += "La red sigue muy polarizada (intenta usar HK con epsilon mayor o memoria para estabilizar). "
        if abs(delta) < 0.05:
            feedback += "La opinión apenas se movió (aumenta el impacto de umbrales u homofilia o la influencia de la regla)."
            
    return score, feedback

def generar_narrativa_final(estrategia_json, objetivo_usuario):
    """Traduce los parámetros matemáticos a climas sociales."""
    client = setup_client()
    prompt = f"""
    Objetivo original del usuario: {objetivo_usuario}
    Secuencia final de intervenciones matemáticas ejecutadas: {json.dumps(estrategia_json, indent=2)}
    
    Genera un reporte sociológico detallado y profesional que explique qué 'clima social', 
    campañas, o eventos de la vida real representa cada fase de estas variables en la red 
    para haber logrado el objetivo con éxito.
    Usa un tono analítico, de estrategia política o sociológica.
    """
    try:
        model_llm = os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
        response = client.chat.completions.create(
            model=model_llm,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        log.error(f"Error generando narrativa: {e}")
        return "El modelo generó la estrategia con éxito, pero falló la generación de la narrativa final por problemas del proveedor LLM."

def buscar_estrategia_inversa(estado_inicial, objetivo_usuario, max_intentos=3, config=None):
    client = setup_client()
    historial_feedback = []
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    
    estrategia_json = {}
    mejor_estrategia = {}
    mejor_historial = None
    mejor_score = -1
    
    model_llm = os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
    
    for intento in range(max_intentos):
        prompt = f"""
        Eres el Arquitecto de Simulación (Modo Inverso).
        Estado inicial de la red: {json.dumps(estado_inicial)}
        Objetivo Deseado: {objetivo_usuario}
        
        Debes generar una programación de intervenciones matemáticas en pasos de tiempo progresivos (ej. 1 a 10, 11 a 20...).
        Modelos permitidos: 'lineal', 'umbral', 'memoria', 'backlash', 'polarizacion', 'hk', 'contagio_competitivo', 'umbral_heterogeneo', 'homofilia'.
        
        Intentos previos y sus fallos: {json.dumps(historial_feedback)}
        
        Responde extrayendo tus fases estructurales estrictamente en un JSON con esta estructura exacta:
        {{
            "interventions": [
                {{
                    "time_start": 1,
                    "time_end": 10,
                    "model_name": "hk",
                    "parameters": {{"epsilon": 0.5}},
                    "fase_rationale": "Reducimos la tensión forzando tolerancia mutua"
                }}
            ]
        }}
        """
        
        try:
            response = client.chat.completions.create(
                model=model_llm,
                messages=[{"role": "system", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            response_content = response.choices[0].message.content
            if response_content.startswith("```json"):
                response_content = response_content.replace("```json", "", 1).replace("```", "")
                
            estrategia_json = json.loads(response_content)
        except Exception as e:
            historial_feedback.append(f"Intento {intento+1}: Error dictado/parseo LLM: {e}")
            continue
            
        historial_sim = run_with_schedule(estado_inicial, estrategia_json, config=cfg)
        
        score, feedback = evaluar_resultado(historial_sim, objetivo_usuario, cfg)
        
        if score > mejor_score:
            mejor_score = score
            mejor_estrategia = estrategia_json
            mejor_historial = historial_sim
            
        if score >= 90:
            narrativa = generar_narrativa_final(estrategia_json, objetivo_usuario)
            return estrategia_json, narrativa, intento + 1, historial_sim
        else:
            historial_feedback.append(f"Intento {intento+1}: {feedback}")
            
    if mejor_score >= 0:
        narrativa = generar_narrativa_final(mejor_estrategia, objetivo_usuario) + "\n\n*(La estrategia es la mejor aproximación, pero puede no haber cumplido todo el objetivo).* "
        return mejor_estrategia, narrativa, max_intentos, mejor_historial
    
    return {"interventions": []}, "Error total en la simulación.", max_intentos, []
