"""
energy_schemas.py — Modelos Pydantic v2 para BeyondSight Energy Engine

Proporciona validación estricta, autocompletado IDE y serialización segura
para todas las configuraciones que cruzan módulos del motor continuo.

Jerarquía de modelos:
    EnergyConfig
    ├── Metadata
    └── EnergyParams
        ├── List[Attractor]
        ├── List[Repeller]
        └── Dynamics
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List


class Attractor(BaseModel):
    """Pozo de potencial que atrae agentes hacia una posición."""

    model_config = ConfigDict(extra="forbid")

    position: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Posición en el espectro [-1, 1]",
    )
    strength: float = Field(
        ...,
        ge=0.5,
        le=4.0,
        description="Profundidad del pozo de atracción",
    )
    label: str = Field(default="Atractor", max_length=40)


class Repeller(BaseModel):
    """Pico de potencial que repele agentes de una posición."""

    model_config = ConfigDict(extra="forbid")

    position: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Posición en el espectro [-1, 1]",
    )
    strength: float = Field(
        ...,
        ge=0.5,
        le=4.0,
        description="Altura del pico de repulsión",
    )
    label: str = Field(default="Repulsor", max_length=40)


class Dynamics(BaseModel):
    """Parámetros dinámicos del motor de Langevin."""

    model_config = ConfigDict(extra="forbid")

    temperature: float = Field(
        ...,
        ge=0.01,
        le=0.20,
        description="Nivel de caos / libre albedrío",
    )
    eta: float = Field(
        default=0.01,
        ge=0.001,
        le=0.1,
        description="Tamaño del paso de integración",
    )
    lambda_social: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Balance red (1.0) vs escenario (0.0)",
    )


class EnergyParams(BaseModel):
    """Parámetros completos del paisaje energético."""

    model_config = ConfigDict(extra="forbid")

    attractors: List[Attractor] = Field(default_factory=list)
    repellers: List[Repeller] = Field(default_factory=list)
    dynamics: Dynamics

    @field_validator("attractors", "repellers", mode="before")
    @classmethod
    def check_unique_positions(cls, v: List) -> List:
        """Rechaza configuraciones con posiciones duplicadas."""
        # v puede ser lista de dicts (antes de la validación del modelo anidado)
        positions = []
        for item in v:
            if isinstance(item, dict):
                positions.append(item.get("position"))
            else:
                positions.append(getattr(item, "position", None))
        if len(positions) != len(set(positions)):
            raise ValueError(
                "Existen atractores/repulsores con la misma posición. "
                "Solapa pozos/picos no permitido."
            )
        return v


class Metadata(BaseModel):
    """Metadatos de la configuración para la UI."""

    model_config = ConfigDict(extra="forbid")

    nombre_ui: str = Field(..., min_length=1, max_length=50)
    descripcion_ui: str = Field(..., min_length=1, max_length=150)
    icono: str = Field(default="🌊", max_length=2)


class EnergyConfig(BaseModel):
    """Configuración completa del motor energético, validada por Pydantic v2."""

    model_config = ConfigDict(extra="forbid")

    metadata: Metadata
    energy_params: EnergyParams

    def to_engine_dict(self) -> dict:
        """
        Devuelve un dict plano 100 % compatible con ``SocialEnergyEngine.step()``.

        Returns
        -------
        dict
            Claves: ``attractors``, ``repellers``, ``dynamics``.
        """
        return {
            "attractors": [a.model_dump() for a in self.energy_params.attractors],
            "repellers": [r.model_dump() for r in self.energy_params.repellers],
            "dynamics": self.energy_params.dynamics.model_dump(),
        }
