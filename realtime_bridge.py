import hashlib
import math
from typing import Any, Dict, List, Tuple

import networkx as nx
import numpy as np

from schemas import GlobalVisualMetrics, VisualAgent, VisualEdge, VisualizationState
from simulator import RANGOS_DISPONIBLES


def _safe_clip(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return float(np.clip(value, lo, hi))


def _opinion_to_color(opinion: float, r_min: float, r_max: float) -> str:
    if r_max <= r_min:
        return "#7F7F7F"
    t = _safe_clip((opinion - r_min) / (r_max - r_min))
    if t <= 0.5:
        local = t / 0.5
        r = 220 + int((127 - 220) * local)
        g = 70 + int((127 - 70) * local)
        b = 70 + int((127 - 70) * local)
    else:
        local = (t - 0.5) / 0.5
        r = 127 + int((70 - 127) * local)
        g = 127 + int((130 - 127) * local)
        b = 127 + int((220 - 127) * local)
    return f"#{r:02X}{g:02X}{b:02X}"


def _friendly_mood_message(conflict_level: float, polarization: float) -> str:
    if conflict_level > 0.7:
        return "¡Cuidado! Se está formando una burbuja de eco."
    if polarization > 0.6:
        return "El sistema está tenso: dos polos compiten por dominar."
    if conflict_level < 0.3 and polarization < 0.3:
        return "Ambiente estable: el grupo se mueve hacia mayor consenso."
    return "¡Parece que el grupo A está convenciendo a todos!"


def _technical_event_message(regla_nombre: str, polarization: float, conflict_level: float) -> str:
    if conflict_level > 0.75:
        return "Shift detected: Regime Transition to Polarized State"
    if polarization > 0.65:
        return f"High polarization sustained under regime: {regla_nombre}"
    if conflict_level < 0.25:
        return f"Stability detected: low conflict under regime {regla_nombre}"
    return f"Regime update: {regla_nombre} with moderated conflict dynamics"


def _compute_seeded_layout(agent_ids: List[str], tick: int) -> Dict[str, Tuple[float, float]]:
    g = nx.Graph()
    for aid in agent_ids:
        g.add_node(aid)

    for i, src in enumerate(agent_ids):
        for j in range(i + 1, len(agent_ids)):
            dst = agent_ids[j]
            h = int(hashlib.md5(f"{src}-{dst}".encode("utf-8")).hexdigest()[:8], 16)
            if h % 9 == 0:
                g.add_edge(src, dst)

    if g.number_of_edges() == 0 and len(agent_ids) > 1:
        for i in range(len(agent_ids) - 1):
            g.add_edge(agent_ids[i], agent_ids[i + 1])

    pos = nx.spring_layout(g, seed=(tick % 1000) + 7, k=0.8 / max(1, math.sqrt(len(agent_ids))), iterations=30)
    normalized = {}
    for aid, (x, y) in pos.items():
        normalized[aid] = (_safe_clip((x + 1.0) / 2.0), _safe_clip((y + 1.0) / 2.0))
    return normalized


def _generate_edges(agents: List[VisualAgent]) -> List[VisualEdge]:
    edges: List[VisualEdge] = []
    for i in range(len(agents)):
        for j in range(i + 1, len(agents)):
            a = agents[i]
            b = agents[j]
            opinion_gap = abs(a.opinion - b.opinion)
            if opinion_gap <= 0.55:
                weight = _safe_clip(1.0 - opinion_gap)
                tension = _safe_clip(opinion_gap)
                bundle = int((i + j) % 5)
                edges.append(
                    VisualEdge(
                        source=a.agent_id,
                        target=b.agent_id,
                        weight=weight,
                        tension=tension,
                        bundled_group=bundle,
                    )
                )
    return edges


def build_visualization_state(
    state: Dict[str, Any],
    tick: int,
    range_name: str,
    session_id: str = "default-session",
    mode: str = "macro",
    previous_state: Dict[str, Any] | None = None,
    n_agents: int = 64,
) -> VisualizationState:
    rango = RANGOS_DISPONIBLES.get(range_name, RANGOS_DISPONIBLES["[0, 1] — Probabilístico"])
    r_min, r_max = float(rango["min"]), float(rango["max"])
    amp = max(1e-9, r_max - r_min)

    global_opinion = float(state.get("opinion", rango["neutro"]))
    confianza = float(state.get("confianza", 0.5))
    pertenencia = float(state.get("pertenencia_grupo", 0.6))
    op_a = float(state.get("opinion_grupo_a", global_opinion))
    op_b = float(state.get("opinion_grupo_b", global_opinion))
    regla = str(state.get("_regla_nombre", "lineal"))

    polarization = _safe_clip(abs(global_opinion - float(rango["neutro"])) / (amp / 2 if amp > 0 else 1.0))
    conflict_level = _safe_clip((abs(op_a - op_b) / amp) * (1.0 - confianza * 0.4))
    mood_index = _safe_clip(1.0 - (0.65 * conflict_level + 0.35 * polarization))

    agent_ids = [f"agent_{i}" for i in range(n_agents)]
    positions = _compute_seeded_layout(agent_ids, tick)

    changed_agent_ids: List[str] = []
    prev_op = global_opinion if previous_state is None else float(previous_state.get("opinion", global_opinion))
    volatility_base = _safe_clip(abs(global_opinion - prev_op) / amp * 2.0)

    agents: List[VisualAgent] = []
    for i, aid in enumerate(agent_ids):
        x, y = positions[aid]
        group_bias = 1.0 if i < int(pertenencia * n_agents) else -1.0
        local_opinion = global_opinion + group_bias * (abs(op_a - op_b) * 0.1)
        local_opinion = float(np.clip(local_opinion, r_min, r_max))
        influence = _safe_clip(0.35 + (0.65 * (1.0 - abs(i - n_agents / 2) / (n_agents / 2))))
        volatility = _safe_clip(volatility_base * (0.7 + 0.3 * (i % 5) / 4))
        local_conflict = _safe_clip(conflict_level * (0.8 + 0.2 * ((i % 7) / 6)))
        local_mood = _safe_clip(mood_index - 0.3 * local_conflict + 0.2 * influence)
        radius = 6.0 + influence * 10.0
        color = _opinion_to_color(local_opinion, r_min, r_max)

        if previous_state is not None and abs(local_opinion - prev_op) > amp * 0.02:
            changed_agent_ids.append(aid)

        agents.append(
            VisualAgent(
                agent_id=aid,
                x=x,
                y=y,
                opinion=local_opinion,
                influence=influence,
                volatility=volatility,
                mood_index=local_mood,
                conflict_score=local_conflict,
                radius=radius,
                color_hex=color,
            )
        )

    edges = _generate_edges(agents)
    event_message = _technical_event_message(regla, polarization, conflict_level)
    narrative_message = _friendly_mood_message(conflict_level, polarization)

    metrics = GlobalVisualMetrics(
        tick=tick,
        global_opinion=global_opinion,
        polarization=polarization,
        conflict_level=conflict_level,
        mood_index=mood_index,
        neutral_reference=float(rango["neutro"]),
        dominant_regime=regla,
        event_message=event_message,
        narrative_message=narrative_message,
        delta_only=previous_state is not None,
    )

    return VisualizationState(
        session_id=session_id,
        mode=mode,
        range_name=range_name,
        agents=agents,
        edges=edges,
        metrics=metrics,
        changed_agent_ids=changed_agent_ids,
    )
