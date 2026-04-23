"""
programmatic_architect.py — Arquitecto Social de BeyondSight (Motor Continuo)

Traduce intenciones del usuario en configuraciones matemáticas validadas
para el EnergyEngine (motor de Langevin de red).

FLUJO:
    1. Búsqueda exacta en ARCHETYPES (instantáneo, sin LLM).
    2. Búsqueda en caché RAM + SQLite (sin LLM).
    3. Llamada one-shot al LLM → validación Pydantic → guardar en caché.
    4. Fallback a arquetipo ``caos_social`` si todo lo anterior falla.

Proveedores LLM soportados: groq | openai | openrouter | ollama
"""

import json
import os
import time
from typing import Optional

import requests

from cache_manager import LandscapeCache
from energy_schemas import EnergyConfig

# ──────────────────────────────────────────────────────────────────────
# Arquetipos predefinidos (sin costo LLM)
# ──────────────────────────────────────────────────────────────────────

ARCHETYPES: dict[str, dict] = {
    "polarizacion_extrema": {
        "metadata": {
            "nombre_ui": "Polarización Extrema",
            "descripcion_ui": "Dos bandos irreconciliables. El centro es tierra de nadie.",
            "icono": "⚡",
        },
        "energy_params": {
            "attractors": [
                {"position": -0.85, "strength": 2.5, "label": "Polo Izquierdo"},
                {"position": 0.85, "strength": 2.5, "label": "Polo Derecho"},
            ],
            "repellers": [
                {"position": 0.0, "strength": 1.5, "label": "Centro / Moderación"}
            ],
            "dynamics": {"temperature": 0.03, "eta": 0.01, "lambda_social": 0.4},
        },
    },
    "polarizacion_moderada": {
        "metadata": {
            "nombre_ui": "División Moderada",
            "descripcion_ui": "Dos grupos, pero con diálogo posible en el centro.",
            "icono": "🔀",
        },
        "energy_params": {
            "attractors": [
                {"position": -0.5, "strength": 1.5, "label": "Grupo A"},
                {"position": 0.5, "strength": 1.5, "label": "Grupo B"},
            ],
            "repellers": [],
            "dynamics": {"temperature": 0.04, "eta": 0.01, "lambda_social": 0.5},
        },
    },
    "consenso_moderado": {
        "metadata": {
            "nombre_ui": "Búsqueda de Consenso",
            "descripcion_ui": "La sociedad tiende a acuerdos. El centro atrae a todos.",
            "icono": "🤝",
        },
        "energy_params": {
            "attractors": [
                {"position": 0.0, "strength": 2.0, "label": "Punto de Acuerdo"}
            ],
            "repellers": [],
            "dynamics": {"temperature": 0.02, "eta": 0.01, "lambda_social": 0.6},
        },
    },
    "consenso_forzado": {
        "metadata": {
            "nombre_ui": "Uniformidad Forzada",
            "descripcion_ui": "Presión institucional fuerte hacia una sola posición.",
            "icono": "📢",
        },
        "energy_params": {
            "attractors": [
                {"position": 0.3, "strength": 3.5, "label": "Posición Oficial"}
            ],
            "repellers": [
                {"position": -0.5, "strength": 2.0, "label": "Disidencia"}
            ],
            "dynamics": {"temperature": 0.01, "eta": 0.02, "lambda_social": 0.2},
        },
    },
    "fragmentacion_3_grupos": {
        "metadata": {
            "nombre_ui": "Tres Facciones",
            "descripcion_ui": "La sociedad se divide en tres grupos que coexisten sin fusionarse.",
            "icono": "🔺",
        },
        "energy_params": {
            "attractors": [
                {"position": -0.7, "strength": 1.5, "label": "Facción A"},
                {"position": 0.0, "strength": 1.2, "label": "Facción B"},
                {"position": 0.7, "strength": 1.5, "label": "Facción C"},
            ],
            "repellers": [],
            "dynamics": {"temperature": 0.04, "eta": 0.01, "lambda_social": 0.5},
        },
    },
    "fragmentacion_4_grupos": {
        "metadata": {
            "nombre_ui": "Cuatro Tribus",
            "descripcion_ui": "Cuatro comunidades con identidades distintas. Alta segmentación.",
            "icono": "🔷",
        },
        "energy_params": {
            "attractors": [
                {"position": -0.8, "strength": 1.2, "label": "Tribu A"},
                {"position": -0.25, "strength": 1.2, "label": "Tribu B"},
                {"position": 0.25, "strength": 1.2, "label": "Tribu C"},
                {"position": 0.8, "strength": 1.2, "label": "Tribu D"},
            ],
            "repellers": [],
            "dynamics": {"temperature": 0.05, "eta": 0.01, "lambda_social": 0.5},
        },
    },
    "caos_social": {
        "metadata": {
            "nombre_ui": "Caos Social",
            "descripcion_ui": "Sin estructura clara. Cada agente actúa por impulso propio.",
            "icono": "🌀",
        },
        "energy_params": {
            "attractors": [],
            "repellers": [],
            "dynamics": {"temperature": 0.15, "eta": 0.01, "lambda_social": 0.3},
        },
    },
    "radicalizacion_progresiva": {
        "metadata": {
            "nombre_ui": "Radicalización Progresiva",
            "descripcion_ui": "Los agentes empiezan al centro pero son jalados hacia los extremos.",
            "icono": "📉",
        },
        "energy_params": {
            "attractors": [
                {"position": -0.9, "strength": 3.0, "label": "Extremo Izq"},
                {"position": 0.9, "strength": 3.0, "label": "Extremo Der"},
            ],
            "repellers": [
                {"position": 0.0, "strength": 2.5, "label": "Moderación"}
            ],
            "dynamics": {"temperature": 0.02, "eta": 0.015, "lambda_social": 0.35},
        },
    },
}

# ──────────────────────────────────────────────────────────────────────
# Caché global (singleton de módulo)
# ──────────────────────────────────────────────────────────────────────

_cache = LandscapeCache()

# ──────────────────────────────────────────────────────────────────────
# System prompt para el LLM
# ──────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Eres un Diseñador de Dinámicas Sociales para BeyondSight.
Tu única tarea es generar configuraciones matemáticas en formato JSON.

REGLAS ESTRICTAS:
- Responde SOLO con JSON válido. Sin texto adicional, sin explicaciones, sin markdown.
- Todos los valores de "position" deben estar en el rango [-1.0, 1.0].
- Los "strength" (fuerza) deben estar entre 0.5 y 4.0.
- "temperature" entre 0.01 y 0.20.
- "lambda_social" entre 0.1 y 0.9.
- No uses posiciones duplicadas en attractors ni en repellers.

ESQUEMA OBLIGATORIO:
{
  "metadata": {
    "nombre_ui": "string (máx 50 chars)",
    "descripcion_ui": "string (máx 150 chars)",
    "icono": "emoji (1-2 chars)"
  },
  "energy_params": {
    "attractors": [{"position": float, "strength": float, "label": "string"}],
    "repellers":  [{"position": float, "strength": float, "label": "string"}],
    "dynamics": {"temperature": float, "eta": 0.01, "lambda_social": float}
  }
}"""


# ──────────────────────────────────────────────────────────────────────
# Llamada al LLM
# ──────────────────────────────────────────────────────────────────────

def call_llm(
    user_goal: str,
    llm_client=None,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> Optional[dict]:
    """
    Realiza una llamada one-shot al LLM para generar una configuración JSON.

    Prueba hasta 2 intentos con backoff de 1 segundo. Devuelve ``None`` si
    falla o si la respuesta no es JSON válido.

    Parameters
    ----------
    user_goal : str
        Intención del usuario (ya normalizada).
    llm_client : Any, optional
        Cliente LLM pre-configurado (no usado actualmente; reservado).
    provider : str, optional
        Proveedor: ``"groq"``, ``"openai"``, ``"openrouter"``, ``"ollama"``.
    api_key : str, optional
        Clave API. Si ``None`` lee de variable de entorno.
    model : str, optional
        ID del modelo. Si ``None`` usa ``LLM_MODEL`` o ``"llama-3.1-8b-instant"``.

    Returns
    -------
    dict | None
        JSON parseado, o ``None`` en caso de error.
    """
    provider = (provider or os.getenv("LLM_PROVIDER", "groq")).lower()
    api_key = api_key or os.getenv(f"{provider.upper()}_API_KEY") or os.getenv(
        "OPENAI_API_KEY"
    )
    model = model or os.getenv("LLM_MODEL", "llama-3.1-8b-instant")

    base_urls: dict[str, str] = {
        "groq": "https://api.groq.com/openai/v1",
        "openai": "https://api.openai.com/v1",
        "openrouter": "https://openrouter.ai/api/v1",
        "ollama": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
    }
    base_url = base_urls.get(provider, base_urls["groq"])

    if provider != "ollama" and not api_key:
        print("[Architect] ⚠️  API key missing. Falling back to archetypes.")
        return None

    prompt = f"Objetivo del usuario: {user_goal}"
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    for attempt in range(2):
        try:
            if provider == "ollama":
                resp = requests.post(
                    f"{base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "system": SYSTEM_PROMPT,
                        "stream": False,
                        "options": {"temperature": 0.2},
                    },
                    timeout=30,
                )
                resp.raise_for_status()
                raw_json: str = resp.json().get("response", "{}")
            else:
                headers: dict[str, str] = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }
                if provider == "openrouter":
                    headers["HTTP-Referer"] = "https://github.com/Adlgr87/BeyondSight"
                    headers["X-Title"] = "BeyondSight Architect"

                resp = requests.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": 0.2,
                        "max_tokens": 500,
                    },
                    timeout=30,
                )
                resp.raise_for_status()
                raw_json = resp.json()["choices"][0]["message"]["content"]

            # Limpiar markdown si el LLM lo incluye
            raw_json = raw_json.strip()
            if raw_json.startswith("```json"):
                raw_json = raw_json[7:]
            if raw_json.startswith("```"):
                raw_json = raw_json[3:]
            if raw_json.endswith("```"):
                raw_json = raw_json[:-3]

            return json.loads(raw_json.strip())

        except requests.exceptions.Timeout:
            if attempt == 0:
                time.sleep(1)
        except Exception as exc:
            print(f"[Architect] 🌐 LLM Error (intento {attempt + 1}): {exc}")
            break

    return None


# ──────────────────────────────────────────────────────────────────────
# Arquitecto principal
# ──────────────────────────────────────────────────────────────────────

class ProgrammaticArchitect:
    """
    Traduce intenciones del usuario en configuraciones de paisaje energético.

    Flujo: Arquetipo → Caché → LLM → Fallback (caos_social).

    Parameters
    ----------
    range_type : str
        ``"bipolar"`` ([-1, 1]) o ``"unipolar"`` ([0, 1]).
    llm_client : Any, optional
        Cliente LLM externo (reservado para integraciones futuras).
    """

    def __init__(
        self,
        range_type: str = "bipolar",
        llm_client=None,
    ) -> None:
        self.range_type = range_type
        self.llm_client = llm_client

    def get_landscape(self, user_goal: str) -> dict:
        """
        Devuelve la configuración del paisaje energético para ``user_goal``.

        Parameters
        ----------
        user_goal : str
            Intención/objetivo descrito por el usuario.

        Returns
        -------
        dict
            Configuración compatible con ``EnergyConfig.model_validate()``.
        """
        goal_clean = user_goal.lower().strip()

        # 1. Arquetipo exacto
        if goal_clean in ARCHETYPES:
            print(f"[Architect] ✅ Arquetipo encontrado: '{goal_clean}'")
            return ARCHETYPES[goal_clean]

        # 2. Caché persistente
        cached = _cache.get(goal_clean)
        if cached:
            print(f"[Architect] 💾 Desde caché: '{goal_clean}'")
            return cached

        # 3. LLM one-shot
        print(f"[Architect] 🤖 Consultando LLM para: '{goal_clean}'")
        llm_result = call_llm(goal_clean, self.llm_client)
        if llm_result and self._validate_config(llm_result):
            _cache.set(goal_clean, llm_result)
            print("[Architect] 💾 Guardado en caché.")
            return llm_result

        # 4. Fallback seguro
        print("[Architect] ⚠️  Fallback a 'caos_social'.")
        return ARCHETYPES["caos_social"]

    def list_available_archetypes(self) -> list[dict]:
        """Devuelve lista de arquetipos con sus metadatos."""
        return [{"key": k, **v["metadata"]} for k, v in ARCHETYPES.items()]

    @staticmethod
    def _validate_config(config: dict) -> bool:
        """Valida una configuración contra el esquema Pydantic."""
        try:
            EnergyConfig.model_validate(config)
            return True
        except Exception as exc:
            print(f"[Architect] ❌ Validación fallida: {exc}")
            return False
