"""
energy_engine.py — Motor de Inferencia Social de BeyondSight
=============================================================
Basado en Dinámica de Langevin de Red (Network Langevin Dynamics).

CONCEPTOS CLAVE:
    - Energía     : Nivel de "tensión" o "incomodidad" de un agente con su posición.
    - Gradiente   : Dirección en que baja más rápido esa tensión (pelota cuesta abajo).
    - Laplaciano  : Matemática de grafos que mide cuánto difiere un agente de sus vecinos.
    - Temperatura : Cuánto "ruido" o libre albedrío tiene cada agente.
    - Clip / Rango: Límites del espectro de opinión. Ej: [-1, 1].

ADVERTENCIAS TÉCNICAS:
    [!] El Laplaciano usa el signo correcto: L = D - A (empuja HACIA los vecinos).
    [!] np.clip() se aplica SIEMPRE al final para respetar los límites del espectro.
    [!] lambda_social controla el balance Red vs. Escenario global.
"""

from typing import Optional

import numpy as np


# ─────────────────────────────────────────────
# 1. MOTOR PRINCIPAL
# ─────────────────────────────────────────────


class SocialEnergyEngine:
    """
    El corazón matemático del módulo Arquitecto Programático de BeyondSight.

    Combina dos fuerzas sobre cada agente:
        • Fuerza del Escenario (E_global): presión institucional, cultural o ideológica.
        • Fuerza de Vecindad  (E_local) : presión de los contactos directos en la red.
    """

    def __init__(
        self,
        range_type: str = "bipolar",
        temperature: float = 0.05,
        lambda_social: float = 0.5,
    ):
        """
        Args:
            range_type    : "bipolar" [-1, 1] o "unipolar" [0, 1].
            temperature   : Nivel de caos / libre albedrío
                            (0.01 = muy ordenado, 0.20 = muy errático).
            lambda_social : Balance red vs. escenario.
                            0.0 = solo importa el escenario global.
                            1.0 = solo importan los vecinos (cámara de eco pura).
                            0.5 = equilibrio (valor por defecto recomendado).
        """
        self.min_val, self.max_val = (
            (0.0, 1.0) if range_type == "unipolar" else (-1.0, 1.0)
        )
        self.temperature   = float(np.clip(temperature,   0.001, 1.0))
        self.lambda_social = float(np.clip(lambda_social, 0.0,   1.0))

    # ── Energía Global (Escenario / Arquetipos) ────────────────────────────

    def energy_global(
        self,
        opinions: np.ndarray,
        attractors: list[dict],
        repellers: Optional[list[dict]] = None,
    ) -> np.ndarray:
        """
        Calcula la energía del escenario para cada agente.

        Args:
            opinions  : Array de posiciones de opinión.
            attractors: Lista de {"position": float, "strength": float}
                        → Zonas de baja energía (donde la sociedad "jala").
            repellers : Lista de {"position": float, "strength": float}
                        → Zonas de alta energía (ideas que la sociedad evita).

        Returns:
            Array de energías, misma forma que opinions.
        """
        energy = np.zeros_like(opinions, dtype=float)

        # Pozos de atracción: potencial cuadrático, mínimo en la posición del atractor
        for att in attractors:
            energy += att["strength"] * np.square(opinions - att["position"])

        # Picos de repulsión: gaussiana invertida (colinas suaves)
        if repellers:
            for rep in repellers:
                sigma = 0.3  # Ancho del pico; ajustable para más precisión
                energy -= rep["strength"] * np.exp(
                    -np.square(opinions - rep["position"]) / (2.0 * sigma ** 2)
                )

        return energy

    def gradient_global(
        self,
        opinions: np.ndarray,
        attractors: list[dict],
        repellers: Optional[list[dict]] = None,
    ) -> np.ndarray:
        """
        Gradiente (dirección de bajada) de la energía global.
        Esto es lo que "mueve" al agente en cada paso.

        Returns:
            Array de gradientes, misma forma que opinions.
        """
        grad = np.zeros_like(opinions, dtype=float)

        # Derivada de strength*(x - c)^2 respecto a x = 2*strength*(x - c)
        for att in attractors:
            grad += 2.0 * att["strength"] * (opinions - att["position"])

        # Derivada del potencial gaussiano invertido:
        # d/dx [-s * exp(-d^2 / 2σ^2)] = s * (d / σ^2) * exp(-d^2 / 2σ^2)
        if repellers:
            for rep in repellers:
                sigma = 0.3
                diff  = opinions - rep["position"]
                grad -= rep["strength"] * (-diff / sigma ** 2) * np.exp(
                    -np.square(diff) / (2.0 * sigma ** 2)
                )

        return grad

    # ── Energía Local (Interacción de Red / Vecindad) ──────────────────────

    def gradient_local(
        self,
        opinions: np.ndarray,
        adjacency_matrix: np.ndarray,
    ) -> np.ndarray:
        """
        Gradiente basado en el Laplaciano del Grafo.

        NOTA TÉCNICA:
            L = D - A  (D = diagonal de grados, A = adyacencia).
            L @ x empuja a cada agente HACIA el promedio de sus vecinos.
            Negarlo en el paso de Langevin mueve el agente hacia sus vecinos.

        En términos simples: si tus amigos piensan diferente, sientes presión
        para acercarte a su posición.

        Returns:
            Array del gradiente local, misma forma que opinions.
        """
        A = adjacency_matrix
        degrees = A.sum(axis=1)
        D = np.diag(degrees)
        L = D - A  # Laplaciano del grafo

        # L @ opinions: cuánto difiere cada agente de sus vecinos ponderados
        return L @ opinions

    # ── Paso de Simulación (Langevin) ─────────────────────────────────────

    def step(
        self,
        opinions: np.ndarray,
        adjacency_matrix: np.ndarray,
        attractors: list[dict],
        repellers: Optional[list[dict]] = None,
        eta: float = 0.01,
    ) -> np.ndarray:
        """
        Ejecuta un paso de tiempo de la simulación de Langevin.

        Fórmula de Langevin de Red:
            x_{t+1} = x_t
                      - eta * [(1 - λ) * ∇E_global + λ * ∇E_local]
                      + sqrt(2 * eta * T) * ε

        Donde:
            eta   = tamaño del paso (velocidad de cambio)
            λ     = lambda_social (peso de la red vs. escenario)
            T     = temperatura (nivel de caos / ruido)
            ε     = ruido gaussiano (libre albedrío)

        Returns:
            Nuevas posiciones de opinión, recortadas al rango válido.
        """
        eta = float(np.clip(eta, 1e-4, 1.0))

        # 1. Gradiente global (escenario/arquetipos)
        g_global = self.gradient_global(opinions, attractors, repellers)

        # 2. Gradiente local (red de vecinos)
        g_local = self.gradient_local(opinions, adjacency_matrix)

        # 3. Score híbrido: combinación ponderada
        score = (1.0 - self.lambda_social) * g_global + self.lambda_social * g_local

        # 4. Ruido gaussiano (libre albedrío / estocasticidad humana)
        noise     = np.random.normal(0.0, 1.0, size=opinions.shape)
        diffusion = np.sqrt(2.0 * eta * self.temperature) * noise

        # 5. Actualización de Langevin (negamos el score porque bajamos la energía)
        new_opinions = opinions - eta * score + diffusion

        # 6. Restricción de rango: nadie puede ir más allá del espectro definido
        return np.clip(new_opinions, self.min_val, self.max_val)

    # ── Simulación completa ────────────────────────────────────────────────

    def run(
        self,
        opinions_init: np.ndarray,
        adjacency_matrix: np.ndarray,
        attractors: list[dict],
        repellers: Optional[list[dict]] = None,
        eta: float = 0.01,
        n_steps: int = 100,
        record_every: int = 1,
    ) -> dict:
        """
        Ejecuta múltiples pasos y devuelve el historial completo.

        Args:
            opinions_init   : Posiciones iniciales de los agentes.
            adjacency_matrix: Matriz de adyacencia (n_agents × n_agents).
            attractors      : Lista de atractores del escenario.
            repellers       : Lista de repulsores del escenario (puede ser None).
            eta             : Tamaño del paso de integración.
            n_steps         : Número de pasos a simular.
            record_every    : Guardar estado cada N pasos.

        Returns:
            Dict con:
                "trajectory"  : lista de arrays de opiniones en cada paso grabado.
                "steps_recorded": lista de índices de paso grabados.
                "metrics"     : métricas finales del sistema.
        """
        opinions = opinions_init.copy().astype(float)
        trajectory = [opinions.copy()]
        steps_recorded = [0]

        for step_i in range(1, n_steps + 1):
            opinions = self.step(opinions, adjacency_matrix, attractors, repellers, eta)
            if step_i % record_every == 0:
                trajectory.append(opinions.copy())
                steps_recorded.append(step_i)

        return {
            "trajectory":     trajectory,
            "steps_recorded": steps_recorded,
            "metrics":        self.system_metrics(
                opinions, adjacency_matrix, attractors, repellers
            ),
        }

    # ── Métricas de Diagnóstico ────────────────────────────────────────────

    def system_metrics(
        self,
        opinions: np.ndarray,
        adjacency_matrix: np.ndarray,
        attractors: list[dict],
        repellers: Optional[list[dict]] = None,
    ) -> dict:
        """
        Calcula indicadores del estado social del sistema.

        Returns dict con:
            tension_total  : Energía media del sistema. Sube = más conflicto.
            polarizacion   : Desviación estándar de opiniones. Alta = sociedad dividida.
            disonancia_red : Diferencia media entre agentes vecinos. Alta = burbujas rotas.
            convergencia   : Qué tan cerca están todos del centro (0 = todos neutrales).
        """
        E      = self.energy_global(opinions, attractors, repellers)
        L_grad = self.gradient_local(opinions, adjacency_matrix)

        return {
            "tension_total" : float(np.mean(E)),
            "polarizacion"  : float(np.std(opinions)),
            "disonancia_red": float(np.mean(np.abs(L_grad))),
            "convergencia"  : float(np.mean(np.abs(opinions))),
        }


# ─────────────────────────────────────────────
# 2. UTILIDADES DE CONSTRUCCIÓN DE GRAFOS
# ─────────────────────────────────────────────


def build_adjacency_from_edges(n_agents: int, edges: list[tuple]) -> np.ndarray:
    """
    Construye una matriz de adyacencia desde una lista de conexiones.

    Args:
        n_agents: Número total de agentes.
        edges   : Lista de tuplas (i, j) — grafo no-dirigido.

    Returns:
        Matriz de adyacencia simétrica (n_agents × n_agents).
    """
    A = np.zeros((n_agents, n_agents))
    for i, j in edges:
        if 0 <= i < n_agents and 0 <= j < n_agents:
            A[i, j] = 1.0
            A[j, i] = 1.0  # No dirigido
    return A


def random_network(
    n_agents: int,
    connectivity: float = 0.3,
    seed: int = 42,
) -> np.ndarray:
    """
    Genera una red aleatoria para pruebas rápidas.

    Args:
        n_agents    : Número de agentes.
        connectivity: Probabilidad de que dos agentes estén conectados (0.0 - 1.0).
                      0.1 = red dispersa | 0.8 = red densa.
        seed        : Semilla para reproducibilidad.

    Returns:
        Matriz de adyacencia simétrica sin auto-conexiones.
    """
    rng = np.random.default_rng(seed)
    A   = rng.random((n_agents, n_agents))
    # Simetrizar y aplicar umbral
    A   = ((A + A.T) / 2.0 > (1.0 - connectivity)).astype(float)
    np.fill_diagonal(A, 0.0)  # Sin auto-conexiones
    return A


def run_energy_simulation(
    archetype: dict,
    n_agents: int = 80,
    n_steps: int = 120,
    connectivity: float = 0.25,
    seed: int = 42,
    range_type: str = "bipolar",
) -> dict:
    """
    Función conveniente que integra arquetipo + EnergyEngine en una sola llamada.

    Args:
        archetype   : Dict de arquetipo (de ARCHETYPES en programmatic_architect.py).
        n_agents    : Número de agentes en la red.
        n_steps     : Pasos de simulación.
        connectivity: Densidad de la red.
        seed        : Semilla aleatoria.
        range_type  : "bipolar" [-1,1] o "unipolar" [0,1].

    Returns:
        Dict con trajectory, steps_recorded y metrics.
    """
    ep      = archetype["energy_params"]
    dyn     = ep["dynamics"]
    min_val = -1.0 if range_type == "bipolar" else 0.0

    rng = np.random.default_rng(seed)
    # Inicializar agentes distribuidos uniformemente (o cerca del centro)
    if range_type == "bipolar":
        opinions_init = rng.uniform(-0.3, 0.3, n_agents)
    else:
        opinions_init = rng.uniform(0.35, 0.65, n_agents)

    adj = random_network(n_agents, connectivity=connectivity, seed=seed)

    engine = SocialEnergyEngine(
        range_type    = range_type,
        temperature   = dyn.get("temperature",   0.05),
        lambda_social = dyn.get("lambda_social", 0.5),
    )

    return engine.run(
        opinions_init    = opinions_init,
        adjacency_matrix = adj,
        attractors       = ep.get("attractors", []),
        repellers        = ep.get("repellers",  []),
        eta              = dyn.get("eta", 0.01),
        n_steps          = n_steps,
        record_every     = max(1, n_steps // 60),  # ~60 frames grabados
    )
