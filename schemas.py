from pydantic import BaseModel, Field
from typing import List, Dict

class Intervention(BaseModel):
    time_start: int = Field(description="Iteración donde inicia esta fase")
    time_end: int = Field(description="Iteración donde termina esta fase")
    model_name: str = Field(description="Nombre del modelo: 'lineal', 'umbral', 'memoria', 'backlash', 'polarizacion', 'hk', 'contagio_competitivo', 'umbral_heterogeneo' u 'homofilia'")
    parameters: Dict[str, float] = Field(description="Parámetros numéricos. Ej: {'epsilon': 0.3} o {'umbral': 0.5}")
    fase_rationale: str = Field(description="Breve justificación sociológica de esta fase")

class StrategyMatrix(BaseModel):
    interventions: List[Intervention] = Field(description="Secuencia temporal de intervenciones")
