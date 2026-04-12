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
