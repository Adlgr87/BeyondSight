"""
BeyondSight — Social Architect (Refactored Central Orquestador)
Clase principal que orquesta motores discrete/continuous, búsqueda inversa y recomendaciones.
"""

import logging
import json
import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from dataclasses import dataclass
from openai import OpenAI

from schemas
