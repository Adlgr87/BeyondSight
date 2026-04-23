from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Any, Dict, List, Optional
import networkx as nx

# Existing Viz Models (upgraded v2)
class Intervention(BaseModel):
    model_config
