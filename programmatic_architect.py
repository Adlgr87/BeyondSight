"""
programmatic_architect.py — Arquitecto Social de BeyondSight
=============================================================
Traduce intenciones del usuario en configuraciones matemáticas para el EnergyEngine.

FILOSOFÍA DE DISEÑO:
    El LLM actúa como ESTRATEGA, no como ejecutor.
    Solo se le consulta cuando el escenario no existe en caché.
    El 95% de las simulaciones corren sin tocar la API del LLM.

FLUJO:
    1. Usuario describe un objetivo social en lenguaje natural.
    2. Architect busca en arquetipos precargados → respuesta inmediata si hay match.
    3. Si no hay match → consulta al LLM UNA SOLA VEZ → guarda el resultado en caché.
    4. Motor de Langevin recibe el JSON y corre autónomamente.

NOTA PARA DESARROLLADORES:
    Reemplaza 'call_llm' con tu cliente real (Groq, OpenRouter, Ollama, etc.)
    La interfaz es intencional: recibe un string, devuelve un string JSON.
"""

import json
import hashlib
import logging
from pathlib import Path
from typing import Optional

log = logging.getLogger("beyondsight")

# ─────────────────────────────────────────────
# 1. ARQUETIPOS PRECARGADOS (Cero Prompts)
# ─────────────────────────────────────────────
# Cada arquetipo es un "paisaje social" con su configuración matemática lista.
# Estos escenarios fueron diseñados y validados manualmente — no requieren LLM.

ARCHETYPES: dict[str, dict] = {

    # ── Escenarios de Polarización ──────────────────────────────────────────

    "polarizacion_extrema": {
        "metadata": {
            "nombre_ui":    "Polarización Extrema",
            "descripcion_ui": "Dos bandos irreconciliables. El centro es tierra de nadie.",
            "icono": "⚡",
        },
        "energy_params": {
            "attractors": [
                {"position": -0.85, "strength": 2.5, "label": "Polo Izquierdo"},
                {"position":  0.85, "strength": 2.5, "label": "Polo Derecho"},
            ],
            "repellers": [
                {"position": 0.0, "strength": 1.5, "label": "Centro / Moderación"},
            ],
            "dynamics": {"temperature": 0.03, "eta": 0.01, "lambda_social": 0.4},
        },
    },

    "polarizacion_moderada": {
        "metadata": {
            "nombre_ui":    "División Moderada",
            "descripcion_ui": "Dos grupos, pero con diálogo posible en el centro.",
            "icono": "🔀",
        },
        "energy_params": {
            "attractors": [
                {"position": -0.5, "strength": 1.5, "label": "Grupo A"},
                {"position":  0.5, "strength": 1.5, "label": "Grupo B"},
            ],
            "repellers": [],
            "dynamics": {"temperature": 0.04, "eta": 0.01, "lambda_social": 0.5},
        },
    },

    # ── Escenarios de Consenso ───────────────────────────────────────────────

    "consenso_moderado": {
        "metadata": {
            "nombre_ui":    "Búsqueda de Consenso",
            "descripcion_ui": "La sociedad tiende a acuerdos. El centro atrae a todos.",
            "icono": "🤝",
        },
        "energy_params": {
            "attractors": [
                {"position": 0.0, "strength": 2.0, "label": "Punto de Acuerdo"},
            ],
            "repellers": [],
            "dynamics": {"temperature": 0.02, "eta": 0.01, "lambda_social": 0.6},
        },
    },

    "consenso_forzado": {
        "metadata": {
            "nombre_ui":    "Uniformidad Forzada",
            "descripcion_ui": "Presión institucional fuerte hacia una sola posición.",
            "icono": "📢",
        },
        "energy_params": {
            "attractors": [
                {"position": 0.3, "strength": 3.5, "label": "Posición Oficial"},
            ],
            "repellers": [
                {"position": -0.5, "strength": 2.0, "label": "Disidencia"},
            ],
            "dynamics": {"temperature": 0.01, "eta": 0.02, "lambda_social": 0.2},
        },
    },

    # ── Escenarios de Fragmentación ─────────────────────────────────────────

    "fragmentacion_3_grupos": {
        "metadata": {
            "nombre_ui":    "Tres Facciones",
            "descripcion_ui": "La sociedad se divide en tres grupos que coexisten sin fusionarse.",
            "icono": "🔺",
        },
        "energy_params": {
            "attractors": [
                {"position": -0.7, "strength": 1.5, "label": "Facción A"},
                {"position":  0.0, "strength": 1.2, "label": "Facción B (Centro)"},
                {"position":  0.7, "strength": 1.5, "label": "Facción C"},
            ],
            "repellers": [],
            "dynamics": {"temperature": 0.04, "eta": 0.01, "lambda_social": 0.5},
        },
    },

    "fragmentacion_4_grupos": {
        "metadata": {
            "nombre_ui":    "Cuatro Tribus",
            "descripcion_ui": "Cuatro comunidades con identidades distintas. Alta segmentación.",
            "icono": "🔷",
        },
        "energy_params": {
            "attractors": [
                {"position": -0.80, "strength": 1.2, "label": "Tribu A"},
                {"position": -0.25, "strength": 1.2, "label": "Tribu B"},
                {"position":  0.25, "strength": 1.2, "label": "Tribu C"},
                {"position":  0.80, "strength": 1.2, "label": "Tribu D"},
            ],
            "repellers": [],
            "dynamics": {"temperature": 0.05, "eta": 0.01, "lambda_social": 0.5},
        },
    },

    # ── Escenarios Dinámicos ─────────────────────────────────────────────────

    "caos_social": {
        "metadata": {
            "nombre_ui":    "Caos Social",
            "descripcion_ui": "Sin estructura clara. Cada agente actúa por impulso propio.",
            "icono": "🌀",
        },
        "energy_params": {
            "attractors": [],   # Sin atractores = energía plana
            "repellers":  [],
            "dynamics": {"temperature": 0.15, "eta": 0.01, "lambda_social": 0.3},
        },
    },

    "radicalizacion_progresiva": {
        "metadata": {
            "nombre_ui":    "Radicalización Progresiva",
            "descripcion_ui": "Los agentes empiezan en el centro pero son jalados hacia los extremos.",
            "icono": "📉",
        },
        "energy_params": {
            "attractors": [
                {"position": -0.9, "strength": 3.0, "label": "Extremo Izquierdo"},
                {"position":  0.9, "strength": 3.0, "label": "Extremo Derecho"},
            ],
            "repellers": [
                {"position": 0.0, "strength": 2.5, "label": "Moderación (Repulsora)"},
            ],
            "dynamics": {"temperature": 0.02, "eta": 0.015, "lambda_social": 0.35},
        },
    },
}

# ─────────────────────────────────────────────
# 2. CACHÉ DE ESCENARIOS PERSONALIZADOS
# ─────────────────────────────────────────────

CACHE_DIR = Path("landscapes")  # Carpeta donde se guardan los JSON generados por el LLM


def _cache_key(user_goal: str) -> str:
    """Genera un ID único y reproducible para cada objetivo del usuario."""
    return hashlib.md5(user_goal.lower().strip().encode()).hexdigest()[:12]


def _load_from_cache(user_goal: str) -> Optional[dict]:
    """Busca si el escenario ya fue generado antes."""
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file = CACHE_DIR / f"{_cache_key(user_goal)}.json"
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            log.warning(f"[Architect] Error leyendo caché: {e}")
    return None


def _save_to_cache(user_goal: str, config: dict) -> None:
    """Guarda el resultado del LLM para no volver a consultarlo."""
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file = CACHE_DIR / f"{_cache_key(user_goal)}.json"
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except OSError as e:
        log.warning(f"[Architect] Error guardando caché: {e}")


# ─────────────────────────────────────────────
# 3. CONECTOR AL LLM (One-Shot)
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """Eres un Diseñador de Dinámicas Sociales para BeyondSight.
Tu única tarea es generar configuraciones matemáticas en formato JSON.

REGLAS ESTRICTAS:
1. Responde SOLO con JSON válido. Sin texto adicional, sin explicaciones, sin markdown.
2. Todos los valores de "position" deben estar en el rango [-1.0, 1.0].
3. Los "strength" (fuerza) deben estar entre 0.5 y 4.0.
4. "temperature" entre 0.01 y 0.20. "lambda_social" entre 0.1 y 0.9.

ESQUEMA OBLIGATORIO:
{
  "metadata": {
    "nombre_ui": "Nombre corto para el usuario",
    "descripcion_ui": "Descripción en español simple (max 15 palabras)",
    "icono": "emoji"
  },
  "energy_params": {
    "attractors": [{"position": float, "strength": float, "label": "string"}],
    "repellers":  [{"position": float, "strength": float, "label": "string"}],
    "dynamics": {
      "temperature": float,
      "eta": 0.01,
      "lambda_social": float
    }
  }
}"""


def call_llm(user_goal: str, llm_client=None) -> Optional[dict]:
    """
    Consulta al LLM una sola vez para generar un escenario nuevo.

    Args:
        user_goal  : Descripción del objetivo social en lenguaje natural.
        llm_client : Tu cliente LLM (Groq, Ollama, OpenRouter, etc.).
                     Si es None, devuelve None y el sistema usa un fallback.

    Returns:
        Dict con la configuración del escenario, o None si falla.
    """
    if llm_client is None:
        return None  # Sin cliente → usar arquetipo más cercano como fallback

    prompt = f"Objetivo del usuario: {user_goal}"

    try:
        # ── Groq / OpenAI-compatible ──────────────────────────────────────
        response = llm_client.chat.completions.create(
            model=getattr(llm_client, "_model", "llama-3.1-8b-instant"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.2,
        )
        raw_json = response.choices[0].message.content

        # Limpiar bloques markdown si el modelo los incluye
        if "```" in raw_json:
            raw_json = raw_json.split("```")[-2].replace("json", "", 1).strip()

        result = json.loads(raw_json)
        return result

    except (json.JSONDecodeError, Exception) as e:
        log.warning(f"[Architect] Error al procesar respuesta del LLM: {e}")
        return None


# ─────────────────────────────────────────────
# 4. ARQUITECTO PRINCIPAL
# ─────────────────────────────────────────────

class ProgrammaticArchitect:
    """
    Orquesta la selección de escenarios sociales para el EnergyEngine.

    Prioridad de resolución (de más rápido a más lento):
        1. Arquetipos precargados  → Instantáneo, sin API.
        2. Caché de disco          → Muy rápido, sin API.
        3. LLM (one-shot)          → Lento, usa API. Solo para casos nuevos.
        4. Fallback a "caos_social" → Si todo falla, algo corre.
    """

    def __init__(self, range_type: str = "bipolar", llm_client=None):
        self.range_type = range_type
        self.llm_client = llm_client

    def get_landscape(self, user_goal: str) -> dict:
        """
        Punto de entrada principal. Recibe lenguaje natural, devuelve configuración.

        Args:
            user_goal : Lo que el usuario quiere simular.
                        Puede ser la clave de un arquetipo o una descripción libre.

        Returns:
            Dict con "energy_params" y "metadata" listo para el EnergyEngine.
        """
        goal_clean = user_goal.lower().strip()

        # ── Paso 1: ¿Es un arquetipo conocido? ──────────────────────────────
        if goal_clean in ARCHETYPES:
            log.info(f"[Architect] ✅ Arquetipo encontrado: '{goal_clean}' (sin API)")
            return ARCHETYPES[goal_clean]

        # ── Paso 2: ¿Búsqueda por nombre_ui? ────────────────────────────────
        for key, arch in ARCHETYPES.items():
            if goal_clean == arch["metadata"]["nombre_ui"].lower():
                log.info(f"[Architect] ✅ Match por nombre_ui: '{key}' (sin API)")
                return arch

        # ── Paso 3: ¿Está en caché? ──────────────────────────────────────────
        cached = _load_from_cache(goal_clean)
        if cached:
            log.info(f"[Architect] 💾 Desde caché: '{goal_clean}' (sin API)")
            return cached

        # ── Paso 4: Llamar al LLM (una sola vez) ────────────────────────────
        log.info(f"[Architect] 🤖 Consultando LLM para: '{goal_clean}'")
        llm_result = call_llm(goal_clean, self.llm_client)
        if llm_result and self._validate_config(llm_result):
            _save_to_cache(goal_clean, llm_result)
            log.info("[Architect] 💾 Resultado guardado en caché.")
            return llm_result

        # ── Paso 5: Fallback ─────────────────────────────────────────────────
        log.warning(
            "[Architect] ⚠️ Fallback a 'caos_social'. "
            "Verifica el LLM o añade el arquetipo manualmente."
        )
        return ARCHETYPES["caos_social"]

    def get_landscape_by_key(self, key: str) -> dict:
        """
        Recupera directamente un arquetipo por su clave interna.

        Args:
            key: Clave del arquetipo (ej. "polarizacion_extrema").

        Returns:
            Configuración del arquetipo, o "caos_social" como fallback.
        """
        return ARCHETYPES.get(key, ARCHETYPES["caos_social"])

    def list_available_archetypes(self) -> list:
        """
        Devuelve los arquetipos en formato amigable para mostrar en la UI.
        Cada item tiene: key, nombre_ui, descripcion_ui, icono.
        """
        return [
            {
                "key": key,
                **arch["metadata"],
            }
            for key, arch in ARCHETYPES.items()
        ]

    @staticmethod
    def _validate_config(config: dict) -> bool:
        """
        Valida que el JSON del LLM tenga la estructura mínima correcta.
        Previene que configuraciones malformadas rompan el motor.

        Args:
            config: Diccionario de configuración a validar.

        Returns:
            True si la configuración es válida, False en caso contrario.
        """
        try:
            params = config["energy_params"]
            assert isinstance(params.get("attractors", []), list)
            assert isinstance(params.get("repellers", []), list)
            dyn = params["dynamics"]
            assert 0.0 < dyn["temperature"] <= 0.5
            assert 0.0 <= dyn["lambda_social"] <= 1.0
            # Verificar que todos los atractores están en rango [-1, 1]
            for att in params.get("attractors", []):
                assert -1.0 <= att["position"] <= 1.0, f"Atractor fuera de rango: {att['position']}"
            # Verificar que todos los repulsores están en rango [-1, 1]
            for rep in params.get("repellers", []):
                assert -1.0 <= rep["position"] <= 1.0, f"Repulsor fuera de rango: {rep['position']}"
            return True
        except (KeyError, AssertionError, TypeError) as e:
            log.warning(f"[Architect] Configuración inválida: {e}")
            return False
