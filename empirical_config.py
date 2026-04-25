"""
BeyondSight — Base Empírica de Calibración
Parámetros derivados de estudios académicos, datasets históricos,
psicología de masas, teoría de juegos y análisis de comportamiento
en redes sociales digitales.

Todos los valores están normalizados al rango bipolar [-1.0, 1.0].
"""

import datetime

# ------------------------------------------------------------
# FLAG DE CARGA
# ------------------------------------------------------------
EMPIRICAL_BASE_LOADED = True

# ============================================================
# DICCIONARIO MAESTRO EMPÍRICO DE BEYONDSIGHT
# Valores normalizados al rango [-1.0, 1.0]
# ============================================================
BEYONDSIGHT_EMPIRICAL_MASTER = {
    "meta": {
        "version": "1.0.0",
        "total_params": 43,
        "coverage_pct": 53.8,
        "generated": datetime.date.today().isoformat(),
    },
    "network_dynamics": {
        "DERIVA_ALGORITMICA": {
            "label": "Aceleración por Deriva Algorítmica",
            "value": 0.45,
            "digital_weight": 1.0,
            "cultural_variance": {
                "latin": 0.40,
                "anglosaxon": 0.50,
                "east_asian": 0.65,
            },
            "source": ["Bonchi et al., 2024-2025"],
            "notes": "Fuerza de arrastre exógena de sistemas de recomendación.",
        },
        "INFLUENCIA_PARASOCIAL": {
            "label": "Asimetría de Influencia Parasocial",
            "value": 0.35,
            "digital_weight": 0.85,
            "cultural_variance": {"latin": 0.50, "anglosaxon": 0.40},
            "source": ["Schramm et al., 2024"],
            "notes": "Preeminencia de influencers sobre expertos.",
        },
        "HOMOFILIA_RED": {
            "label": "Homofilia en Redes Digitales",
            "value": None,
            "digital_weight": 0.9,
            "cultural_variance": {},
            "source": [],
            "notes": "pending_empirical_data",
        },
        "AMPLIFICACION_VIRAL": {
            "label": "Factor de Amplificación Viral",
            "value": None,
            "digital_weight": 1.0,
            "cultural_variance": {},
            "source": [],
            "notes": "pending_empirical_data",
        },
    },
    "temporal": {
        "MEDIA_VIDA_DIGITAL": {
            "value": 0.0,  # Neutralidad en escala logarítmica normalizada
            "normalization": {"original_scale": "horas", "original_max": 168.0},
            "notes": "Decaimiento de la atención en narrativas virales.",
        },
        "ELASTICIDAD_CONFIANZA": {
            "value": -0.25,
            "notes": "Efecto de la inflación sostenida en la confianza institucional.",
        },
        "CICLO_ATENCION": {
            "value": None,
            "notes": "pending_empirical_data",
        },
        "FATIGA_OUTRAGE": {
            "value": None,
            "notes": "pending_empirical_data",
        },
    },
    "individual_psychology": {
        "SESGO_CONFIRMACION": {
            "label": "Sesgo de Confirmación Cognitivo",
            "value": 0.38,
            "cultural_variance": {"latin": 0.35, "anglosaxon": 0.40, "east_asian": 0.30},
            "source": ["Nickerson, 1998", "Sunstein, 2009"],
            "notes": "Resistencia a información contraria a creencias previas.",
        },
        "EFECTO_BACKFIRE": {
            "label": "Efecto Backfire (Refuerzo por Contradicción)",
            "value": 0.22,
            "source": ["Nyhan & Reifler, 2010"],
            "notes": "Cuando la corrección refuerza la creencia errónea original.",
        },
        "INOCULACION_COGNITIVA": {
            "label": "Resistencia por Inoculación Cognitiva",
            "value": -0.30,
            "source": ["van der Linden et al., 2022"],
            "notes": "Valor negativo: reduce adopción de desinformación.",
        },
        "DISONANCIA_COGNITIVA": {
            "value": None,
            "notes": "pending_empirical_data",
        },
        "PENSAMIENTO_RAPIDO": {
            "value": None,
            "notes": "pending_empirical_data",
        },
    },
    "mass_psychology": {
        "CONTAGIO_EMOCIONAL": {
            "label": "Contagio Emocional en Redes",
            "value": 0.42,
            "digital_weight": 0.95,
            "source": ["Kramer et al., 2014"],
            "notes": "Propagación de estados emocionales vía exposición pasiva.",
        },
        "CASCADA_INFORMACIONAL": {
            "label": "Cascada Informacional",
            "value": 0.55,
            "source": ["Bikhchandani et al., 1992"],
            "notes": "Adopción de creencias por imitación sin evidencia propia.",
        },
        "POLARIZACION_GRUPO": {
            "label": "Polarización por Deliberación Grupal",
            "value": 0.48,
            "source": ["Sunstein, 2002"],
            "notes": "Los grupos extremizan sus posiciones al deliberar internamente.",
        },
        "EFECTO_MANADA": {
            "value": None,
            "notes": "pending_empirical_data",
        },
        "SILENCIO_ESPIRAL": {
            "value": None,
            "notes": "pending_empirical_data",
        },
    },
    "cultural_variables": {
        "INDIVIDUALISMO_COLECTIVISMO": {
            "label": "Eje Individualismo-Colectivismo (Hofstede)",
            "value": 0.0,  # Neutralidad: varía radicalmente por cultura
            "cultural_variance": {
                "anglosaxon": 0.75,
                "latin": -0.10,
                "east_asian": -0.55,
                "middle_east": -0.30,
                "south_asian": -0.40,
                "subsaharan_africa": -0.25,
            },
            "source": ["Hofstede et al., 2010"],
            "notes": "Positivo=individualismo, negativo=colectivismo.",
        },
        "DISTANCIA_PODER": {
            "label": "Distancia al Poder",
            "value": None,
            "notes": "pending_empirical_data",
        },
        "EVITACION_INCERTIDUMBRE": {
            "value": None,
            "notes": "pending_empirical_data",
        },
    },
    "social_status": {
        "EFECTO_CLASE_SOCIAL": {
            "label": "Modulación por Clase Social",
            "value": None,
            "notes": "pending_empirical_data",
        },
        "BRECHA_GENERACIONAL": {
            "label": "Diferencial de Opinión por Generación",
            "value": None,
            "notes": "pending_empirical_data",
        },
    },
    "gender": {
        "DIFERENCIAL_GENERO": {
            "label": "Diferencial de Opinión por Género",
            "value": None,
            "notes": "pending_empirical_data",
        },
    },
    "game_theory": {
        "EQUILIBRIO_NASH_SOCIAL": {
            "label": "Tendencia al Equilibrio de Nash en Interacciones Sociales",
            "value": 0.60,
            "source": ["Nash, 1950", "Gintis, 2009"],
            "notes": "Utilidad de unirse al consenso mayoritario.",
        },
        "COSTO_DISIDENCIA": {
            "label": "Costo Social de la Disidencia",
            "value": -0.50,
            "source": ["Noelle-Neumann, 1993"],
            "notes": "Valor negativo: penalización por posición contramayoritaria.",
        },
        "DILEMA_PRISIONERO_SOCIAL": {
            "value": None,
            "notes": "pending_empirical_data",
        },
        "CAZA_CIERVO": {
            "value": None,
            "notes": "pending_empirical_data",
        },
    },
}

# ============================================================
# PARÁMETROS DE EJECUCIÓN DEL MOTOR
# ============================================================
BEYONDSIGHT_RUNTIME_PARAMS: dict = {
    "temperature": 0.45,             # Caos/Irracionalidad (backfire vs inoculación)
    "social_influence_lambda": 0.58,  # Peso de la red vs convicción propia
    "attractor_depth": 0.75,          # Fuerza de la narrativa dominante
    "repeller_strength": -0.45,       # Animosidad out-group (prosocialidad invertida)
    "payoff_coordination": 0.602,     # Utilidad de unirse al consenso
    "payoff_defection": -0.5,         # Costo de la disidencia
    "narrative_decay_rate": 0.0,      # Media-vida de influencia narrativa (neutralidad activa)
    "saturation_threshold": 0.0,      # Punto de rechazo por sobreexposición (neutralidad activa)
    "cultural_profile": "mixed",
    "validation_flags": [],
}

# Parámetros null del maestro que requieren datos empíricos adicionales
_NULL_PARAMS = [
    ("network_dynamics", "HOMOFILIA_RED"),
    ("network_dynamics", "AMPLIFICACION_VIRAL"),
    ("temporal", "CICLO_ATENCION"),
    ("temporal", "FATIGA_OUTRAGE"),
    ("individual_psychology", "DISONANCIA_COGNITIVA"),
    ("individual_psychology", "PENSAMIENTO_RAPIDO"),
    ("mass_psychology", "EFECTO_MANADA"),
    ("mass_psychology", "SILENCIO_ESPIRAL"),
    ("cultural_variables", "DISTANCIA_PODER"),
    ("cultural_variables", "EVITACION_INCERTIDUMBRE"),
    ("social_status", "EFECTO_CLASE_SOCIAL"),
    ("social_status", "BRECHA_GENERACIONAL"),
    ("gender", "DIFERENCIAL_GENERO"),
    ("game_theory", "DILEMA_PRISIONERO_SOCIAL"),
    ("game_theory", "CAZA_CIERVO"),
]

# Populate validation_flags with pending null params (never use 0.0 as default)
for _cat, _pid in _NULL_PARAMS:
    _entry = BEYONDSIGHT_EMPIRICAL_MASTER.get(_cat, {}).get(_pid, {})
    if _entry.get("value") is None:
        BEYONDSIGHT_RUNTIME_PARAMS["validation_flags"].append(
            f"{_cat}.{_pid}: pending_empirical_data"
        )


# ============================================================
# FUNCIONES DE ACCESO
# ============================================================

def get_runtime_params(cultural_profile: str = "mixed") -> dict:
    """
    Returns a complete runtime parameter dictionary with cultural modifiers applied.

    Applies cultural variance modifiers from BEYONDSIGHT_EMPIRICAL_MASTER over
    the base values in BEYONDSIGHT_RUNTIME_PARAMS.  The ``mixed`` profile uses
    the unmodified base values.  Unknown profiles fall back to ``mixed``.

    Args:
        cultural_profile: One of ``"mixed"``, ``"latin"``, ``"anglosaxon"``,
            ``"east_asian"``, ``"middle_east"``, ``"south_asian"``,
            ``"subsaharan_africa"``.  Defaults to ``"mixed"``.

    Returns:
        A new dict with all runtime parameters; values 0.0 and negative values
        are preserved without modification (they represent active neutrality and
        active repellers respectively).
    """
    params = dict(BEYONDSIGHT_RUNTIME_PARAMS)
    params["validation_flags"] = list(BEYONDSIGHT_RUNTIME_PARAMS["validation_flags"])
    params["cultural_profile"] = cultural_profile

    if cultural_profile == "mixed":
        return params

    # Apply known cultural variance to runtime params that have direct mapping
    # DERIVA_ALGORITMICA → temperature (caos social amplificado por algoritmos)
    deriva = BEYONDSIGHT_EMPIRICAL_MASTER["network_dynamics"]["DERIVA_ALGORITMICA"]
    if cultural_profile in deriva.get("cultural_variance", {}):
        cultural_val = deriva["cultural_variance"][cultural_profile]
        base_val = deriva["value"]
        delta = cultural_val - base_val
        params["temperature"] = float(
            max(-1.0, min(1.0, params["temperature"] + delta))
        )

    # INFLUENCIA_PARASOCIAL → social_influence_lambda
    parasocial = BEYONDSIGHT_EMPIRICAL_MASTER["network_dynamics"]["INFLUENCIA_PARASOCIAL"]
    if cultural_profile in parasocial.get("cultural_variance", {}):
        cultural_val = parasocial["cultural_variance"][cultural_profile]
        base_val = parasocial["value"]
        delta = cultural_val - base_val
        params["social_influence_lambda"] = float(
            max(-1.0, min(1.0, params["social_influence_lambda"] + delta))
        )

    return params


def get_param(category: str, param_id: str) -> dict:
    """
    Returns a parameter entry from BEYONDSIGHT_EMPIRICAL_MASTER by category and ID.

    Args:
        category: Top-level key in BEYONDSIGHT_EMPIRICAL_MASTER
            (e.g. ``"network_dynamics"``).
        param_id: Parameter key within the category
            (e.g. ``"DERIVA_ALGORITMICA"``).

    Returns:
        The parameter dictionary for the requested entry.

    Raises:
        KeyError: If ``category`` or ``param_id`` does not exist in the master
            dictionary, with a descriptive message.
    """
    if category not in BEYONDSIGHT_EMPIRICAL_MASTER:
        raise KeyError(
            f"Category '{category}' not found in BEYONDSIGHT_EMPIRICAL_MASTER. "
            f"Available categories: {list(BEYONDSIGHT_EMPIRICAL_MASTER.keys())}"
        )
    category_data = BEYONDSIGHT_EMPIRICAL_MASTER[category]
    if not isinstance(category_data, dict) or param_id not in category_data:
        raise KeyError(
            f"Parameter '{param_id}' not found in category '{category}'. "
            f"Available params: {list(category_data.keys()) if isinstance(category_data, dict) else '(not a dict)'}"
        )
    return category_data[param_id]
