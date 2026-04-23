"""
energy_engine.py — Motor de Inferencia Social de BeyondSight
=============================================================
Basado en Dinámica de Langevin de Red (Network Langevin Dynamics).

CONCEPTOS CLAVE:
  - Energía      : Nivel de "tensión" o "incomodidad" de un agente con su posición actual.
  - Gradiente    : La dirección en que baja más rápido esa tensión.
  - Laplaciano   : Matemática de grafos que mide cuánto difiere un agente de sus vecinos.
  - Temperatura  : Cuánto "ruido" o libre albedrío tiene cada agente.
  - Clip / Rango : Límites del espectro de opinión. Ej: [-1, 1].

ADVERTENCIAS TÉCNICAS:
  [!] El Laplaciano usa el signo correcto: L = D - A (empuja HACIA los vecinos).
  [!] np.clip() se aplica SIEMPRE al final para respetar los límites del espectro.
  [!] lambda_social controla el balance Red vs. Escenario global.
"""

import numpy as np
from typing import Optional


# ─────────────────────────────────────────────
# 1. MOTOR PRINCIPAL
# ─────────────────────────────────────────────

class SocialEnergyEngine:
    """
    El corazón matemático de BeyondSight — Motor Langevin de Red.

    Combina dos fuerzas sobre cada agente:
      • Fuerza del Escenario (E_global): presión institucional, cultural o ideológica.
      • Fuerza de Vecindad  (E_local) : presión de los contactos directos en la red social.
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
            temperature   : Nivel de caos / libre albedrío (0.01 = muy ordenado, 0.2 = caótico).
            lambda_social : Balance red vs. escenario.
                            0.0 = solo el escenario global (propaganda pura).
                            1.0 = solo los vecinos (cámara de eco pura).
                            0.5 = equilibrio (valor por defecto recomendado).
        """
        self.min_val, self.max_val = (0.0, 1.0) if range_type == "unipolar" else (-1.0, 1.0)
        self.temperature = float(temperature)
        self.lambda_social = float(np.clip(lambda_social, 0.0, 1.0))

    # ── Energía Global (Escenario / Arquetipos) ──────────────────────────────

    def energy_global(
        self,
        opinions: np.ndarray,
        attractors: list,
        repellers: Optional[list] = None,
    ) -> np.ndarray:
        """
        Calcula la energía del escenario para cada agente.

        Args:
            opinions  : Array de opiniones actuales (shape: n_agents,).
            attractors: Lista de {"position": float, "strength": float, "label": str}
                        → Zonas de baja energía (donde la sociedad "jala").
            repellers : Lista de {"position": float, "strength": float, "label": str}
                        → Zonas de alta energía (ideas que la sociedad evita activamente).

        Returns:
            Array de energías por agente (shape: n_agents,).
        """
        opinions = np.asarray(opinions, dtype=float)
        energy = np.zeros_like(opinions)

        # Pozos de atracción: energía baja cerca del centro del pozo
        for att in (attractors or []):
            energy += att["strength"] * np.square(opinions - att["position"])

        # Picos de repulsión: energía alta cerca del repulsor
        # Potencial invertido (gaussiana negativa) para crear colinas suaves
        if repellers:
            for rep in repellers:
                sigma = 0.3  # Ancho del pico; ajustable
                energy -= rep["strength"] * np.exp(
                    -np.square(opinions - rep["position"]) / (2 * sigma ** 2)
                )

        return energy

    def gradient_global(
        self,
        opinions: np.ndarray,
        attractors: list,
        repellers: Optional[list] = None,
    ) -> np.ndarray:
        """
        Gradiente (dirección de bajada) de la energía global.
        Esto es lo que 'mueve' al agente en cada paso de Langevin.

        Args:
            opinions  : Array de opiniones actuales.
            attractors: Lista de atractores.
            repellers : Lista de repulsores.

        Returns:
            Array de gradientes por agente.
        """
        opinions = np.asarray(opinions, dtype=float)
        grad = np.zeros_like(opinions)

        # Derivada de s*(x - c)^2 respecto a x = 2*s*(x - c)
        for att in (attractors or []):
            grad += 2.0 * att["strength"] * (opinions - att["position"])

        # Derivada del potencial gaussiano invertido
        if repellers:
            for rep in repellers:
                sigma = 0.3
                diff = opinions - rep["position"]
                grad -= rep["strength"] * (-diff / sigma ** 2) * np.exp(
                    -np.square(diff) / (2 * sigma ** 2)
                )

        return grad

    # ── Energía Local (Interacción de Red / Vecindad) ───────────────────────

    def gradient_local(
        self,
        opinions: np.ndarray,
        adjacency_matrix: np.ndarray,
    ) -> np.ndarray:
        """
        Gradiente basado en el Laplaciano del Grafo.

        NOTA TÉCNICA:
            L = D - A  donde D = matriz diagonal de grados, A = adyacencia.
            El gradiente L @ x empuja a cada agente HACIA el promedio de sus vecinos.
            Signo positivo en el gradiente = la energía SUBE si difiero de mis vecinos.
            Al negarlo en el paso Langevin, el agente SE MUEVE hacia sus vecinos.

        Args:
            opinions        : Array de opiniones actuales.
            adjacency_matrix: Matriz de adyacencia cuadrada (n x n).

        Returns:
            Gradiente local por agente.
        """
        opinions = np.asarray(opinions, dtype=float)
        A = np.asarray(adjacency_matrix, dtype=float)
        D = np.diag(A.sum(axis=1))   # Grado de cada nodo
        L = D - A                     # Laplaciano del grafo
        return L @ opinions           # cuánto difiere cada agente de sus vecinos

    # ── Paso de Simulación (Langevin) ─────────────────────────────────────────

    def step(
        self,
        opinions: np.ndarray,
        adjacency_matrix: np.ndarray,
        attractors: list,
        repellers: Optional[list] = None,
        eta: float = 0.01,
    ) -> np.ndarray:
        """
        Ejecuta un paso de tiempo de la simulación.

        Fórmula de Langevin de Red:
            x_{t+1} = x_t
                    - eta * [ (1 - λ) * ∇E_global + λ * ∇E_local ]
                    + sqrt(2 * eta * T) * ε

        Donde:
            eta  = tamaño del paso (velocidad de cambio)
            λ    = lambda_social (peso de la red vs. escenario)
            T    = temperatura (nivel de caos / ruido)
            ε    = ruido gaussiano (libre albedrío)

        Args:
            opinions        : Array de opiniones actuales.
            adjacency_matrix: Matriz de adyacencia.
            attractors      : Lista de atractores del escenario.
            repellers       : Lista de repulsores del escenario.
            eta             : Tamaño del paso de integración.

        Returns:
            Nuevas posiciones de opinión, recortadas al rango válido.
        """
        opinions = np.asarray(opinions, dtype=float)

        # 1. Gradiente global (escenario/arquetipos)
        g_global = self.gradient_global(opinions, attractors, repellers)

        # 2. Gradiente local (red de vecinos)
        g_local = self.gradient_local(opinions, adjacency_matrix)

        # 3. Score híbrido: combinación ponderada
        score = (1.0 - self.lambda_social) * g_global + self.lambda_social * g_local

        # 4. Ruido gaussiano (libre albedrío / estocasticidad humana)
        noise = np.random.normal(0, 1, size=opinions.shape)
        diffusion = np.sqrt(2.0 * eta * self.temperature) * noise

        # 5. Actualización de Langevin (negamos el score porque bajamos la energía)
        new_opinions = opinions - eta * score + diffusion

        # 6. Restricción de rango: nadie puede ir más allá del espectro definido
        return np.clip(new_opinions, self.min_val, self.max_val)

    # ── Métricas de Diagnóstico ──────────────────────────────────────────────

    def system_metrics(
        self,
        opinions: np.ndarray,
        adjacency_matrix: np.ndarray,
        attractors: list,
        repellers: Optional[list] = None,
    ) -> dict:
        """
        Calcula indicadores del estado social del sistema.

        Returns dict con:
            tension_total  : Energía media del sistema. Sube = más conflicto.
            polarizacion   : Desviación estándar de opiniones. Alta = sociedad dividida.
            disonancia_red : Diferencia media entre agentes vecinos. Alta = burbujas rotas.
            convergencia   : Qué tan cerca están todos del centro (0 = todos neutrales).
        """
        opinions = np.asarray(opinions, dtype=float)
        E = self.energy_global(opinions, attractors, repellers)
        L_grad = self.gradient_local(opinions, adjacency_matrix)

        return {
            "tension_total":  float(np.mean(E)),
            "polarizacion":   float(np.std(opinions)),
            "disonancia_red": float(np.mean(np.abs(L_grad))),
            "convergencia":   float(np.mean(np.abs(opinions))),
        }


# ─────────────────────────────────────────────
# 2. UTILIDADES DE CONSTRUCCIÓN DE GRAFOS
# ─────────────────────────────────────────────

def build_adjacency_from_edges(n_agents: int, edges: list) -> np.ndarray:
    """
    Construye una matriz de adyacencia desde una lista de conexiones.

    Args:
        n_agents : Número total de agentes.
        edges    : Lista de tuplas (i, j) indicando quién conoce a quién.
                   El grafo es no-dirigido (la influencia va en ambas direcciones).

    Returns:
        Matriz de adyacencia simétrica (n_agents × n_agents).
    """
    A = np.zeros((n_agents, n_agents))
    for i, j in edges:
        if 0 <= i < n_agents and 0 <= j < n_agents:
            A[i, j] = 1.0
            A[j, i] = 1.0  # No dirigido
    return A


def random_network(n_agents: int, connectivity: float = 0.3, seed: int = 42) -> np.ndarray:
    """
    Genera una red aleatoria para pruebas rápidas.

    Args:
        n_agents    : Número de agentes.
        connectivity: Probabilidad de que dos agentes estén conectados (0.0 – 1.0).
                      0.1 = red dispersa (como Twitter sin seguirse mutuamente)
                      0.8 = red densa (como un grupo pequeño donde todos se conocen)
        seed        : Semilla aleatoria para reproducibilidad.

    Returns:
        Matriz de adyacencia simétrica sin auto-conexiones.
    """
    rng = np.random.default_rng(seed)
    A = rng.random((n_agents, n_agents))
    A = ((A + A.T) / 2.0 > (1.0 - connectivity)).astype(float)
    np.fill_diagonal(A, 0.0)  # Sin auto-conexiones
    return A


def run_energy_simulation(
    n_agents: int,
    steps: int,
    attractors: list,
    repellers: Optional[list],
    dynamics: dict,
    range_type: str = "bipolar",
    connectivity: float = 0.3,
    seed: int = 42,
) -> dict:
    """
    Ejecuta una simulación completa con el EnergyEngine y devuelve el historial.

    Args:
        n_agents   : Número de agentes.
        steps      : Pasos de tiempo a simular.
        attractors : Lista de atractores.
        repellers  : Lista de repulsores.
        dynamics   : Dict con "temperature", "eta", "lambda_social".
        range_type : "bipolar" o "unipolar".
        connectivity: Densidad de la red aleatoria.
        seed       : Semilla para reproducibilidad.

    Returns:
        Dict con "opinions_history" (steps+1 × n_agents), "metrics_history", "final_metrics".
    """
    temperature   = dynamics.get("temperature", 0.05)
    eta           = dynamics.get("eta", 0.01)
    lambda_social = dynamics.get("lambda_social", 0.5)

    engine = SocialEnergyEngine(
        range_type=range_type,
        temperature=temperature,
        lambda_social=lambda_social,
    )

    # Inicialización: opiniones distribuidas uniformemente en el rango
    rng = np.random.default_rng(seed)
    lo, hi = engine.min_val, engine.max_val
    opinions = rng.uniform(lo, hi, size=n_agents)

    adj = random_network(n_agents, connectivity=connectivity, seed=seed)

    opinions_history = [opinions.copy()]
    metrics_history  = []

    for _ in range(steps):
        opinions = engine.step(opinions, adj, attractors, repellers, eta=eta)
        opinions_history.append(opinions.copy())
        metrics_history.append(
            engine.system_metrics(opinions, adj, attractors, repellers)
        )

    return {
        "opinions_history": opinions_history,
        "metrics_history":  metrics_history,
        "final_metrics":    metrics_history[-1] if metrics_history else {},
        "adjacency_matrix": adj,
    }
