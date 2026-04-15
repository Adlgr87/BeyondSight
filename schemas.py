from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class Intervention(BaseModel):
    time_start: int = Field(description="Iteración donde inicia esta fase")
    time_end: int = Field(description="Iteración donde termina esta fase")
    model_name: str = Field(
        description=(
            "Nombre del modelo: 'lineal', 'umbral', 'memoria', 'backlash', "
            "'polarizacion', 'hk', 'contagio_competitivo', 'umbral_heterogeneo' u 'homofilia'"
        )
    )
    parameters: Dict[str, Any] = Field(
        description=(
            "Parámetros numéricos. Ej: {'epsilon': 0.3} o {'umbral': 0.5}. "
            "En modo corporativo puede incluir 'target_nodes': lista de IDs de nodos "
            "a intervenir directamente (ej. líderes de opinión en la empresa)."
        )
    )
    fase_rationale: str = Field(description="Breve justificación sociológica/organizacional de esta fase")
    target_nodes: Optional[List[str]] = Field(
        default=None,
        description=(
            "Opcional. Lista de IDs de nodos específicos a intervenir "
            "(líderes informales, directivos clave). Solo relevante en modo corporativo."
        ),
    )


class StrategyMatrix(BaseModel):
    interventions: List[Intervention] = Field(description="Secuencia temporal de intervenciones")


class VisualAgent(BaseModel):
    agent_id: str = Field(description="Identificador único del agente")
    x: float = Field(description="Posición X normalizada del agente")
    y: float = Field(description="Posición Y normalizada del agente")
    opinion: float = Field(description="Opinión actual del agente en el rango activo")
    influence: float = Field(description="Influencia normalizada [0,1]")
    volatility: float = Field(description="Volatilidad normalizada [0,1]")
    mood_index: float = Field(description="Índice emocional [0,1]")
    conflict_score: float = Field(description="Conflicto local [0,1]")
    radius: float = Field(description="Radio visual del agente")
    color_hex: str = Field(description="Color serializado en formato HEX")


class VisualEdge(BaseModel):
    source: str = Field(description="ID del agente de origen")
    target: str = Field(description="ID del agente de destino")
    weight: float = Field(description="Peso normalizado de influencia [0,1]")
    tension: float = Field(description="Tensión social en la arista [0,1]")
    bundled_group: int = Field(description="Grupo de bundling para render técnico")


class GlobalVisualMetrics(BaseModel):
    tick: int = Field(description="Iteración/tick actual")
    global_opinion: float = Field(description="Opinión global promedio")
    polarization: float = Field(description="Polarización global normalizada [0,1]")
    conflict_level: float = Field(description="Conflicto agregado [0,1]")
    mood_index: float = Field(description="Mood global [0,1]")
    neutral_reference: float = Field(description="Valor de referencia neutral para el rango")
    dominant_regime: str = Field(description="Régimen/mecánica dominante detectada")
    event_message: str = Field(description="Mensaje técnico corto para ticker de eventos")
    narrative_message: str = Field(description="Mensaje amigable para capa cartoon")
    delta_only: bool = Field(description="True si el frame fue calculado como delta")


class VisualizationState(BaseModel):
    session_id: str = Field(description="ID de la sesión de simulación")
    mode: str = Field(description="Modo de simulación: macro/corporativo")
    range_name: str = Field(description="Nombre del rango activo")
    agents: List[VisualAgent] = Field(description="Estado visual de los agentes")
    edges: List[VisualEdge] = Field(description="Conexiones visuales serializadas")
    metrics: GlobalVisualMetrics = Field(description="Métricas globales serializadas")
    changed_agent_ids: List[str] = Field(
        default_factory=list,
        description="IDs modificados respecto al tick previo para envío en delta",
    )
