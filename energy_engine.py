"""
energy_engine.py — Motor de Dinámica de Langevin de Red para BeyondSight
Implementa: atractores (pozos), repulsores (picos), presión social Laplaciana,
integración estocástica y métricas del sistema.

Ecuación de Langevin discretizada:
    x_{t+1} = x_t - η·∇E(x_t) + √(2ηT)·ε_t

donde:
    E(x) = -Σ_i strength_i · exp(-((x - pos_i)/σ)²)   [atractores]
          + Σ_j strength_j · exp(-((x - pos_j)/σ)²)    [repulsores]
    ε_t ~ N(0, 1)   (ruido blanco gaussiano)
    η   = paso de integración (eta)
    T   = temperatura (libre albedrío)

La presión social se añade vía Laplaciano:
    social_force = -λ · L · x   donde L = D - A (Laplaciano de la red)
"""

import numpy as np
from typing import Optional


# ──────────────────────────────────────────────
# Helpers de red
# ──────────────────────────────────────────────

def random_network(
    n: int,
    connectivity: float = 0.3,
    seed: Optional[int] = None,
) -> np.ndarray:
    """
    Genera una red aleatoria de Erdős–Rényi simétrica sin auto-conexiones.

    Parameters
    ----------
    n : int
        Número de agentes.
    connectivity : float
        Probabilidad de enlace entre cada par de nodos (0–1).
    seed : int, optional
        Semilla para reproducibilidad.

    Returns
    -------
    np.ndarray
        Matriz de adyacencia (n, n), simétrica, diagonal = 0.
    """
    rng = np.random.default_rng(seed)
    upper = rng.random((n, n))
    mask = upper < connectivity
    # Simetrizar y borrar diagonal
    sym = np.triu(mask, k=1)
    adj = (sym + sym.T).astype(float)
    return adj


def _laplacian(adj: np.ndarray) -> np.ndarray:
    """Calcula el Laplaciano L = D - A de la red."""
    degree = adj.sum(axis=1)
    return np.diag(degree) - adj


# ──────────────────────────────────────────────
# Motor principal
# ──────────────────────────────────────────────

class SocialEnergyEngine:
    """
    Motor continuo de dinámica social basado en Langevin de Red.

    Atractores crean pozos de energía (posiciones estables).
    Repulsores crean picos de energía (posiciones inestables/repelidas).
    La presión social empuja las opiniones hacia el promedio de vecinos.

    Parameters
    ----------
    range_type : str
        ``"bipolar"`` → opiniones en [-1, 1].
        ``"unipolar"`` → opiniones en [0, 1].
    temperature : float
        Nivel de ruido estocástico (libre albedrío). Rango: [0.01, 0.20].
    lambda_social : float
        Balance entre presión institucional (0.0) y cámara de eco (1.0).
    sigma : float
        Ancho de los pozos/picos gaussianos. Por defecto 0.3.
    """

    _SIGMA_DEFAULT = 0.3

    def __init__(
        self,
        range_type: str = "bipolar",
        temperature: float = 0.05,
        lambda_social: float = 0.5,
        sigma: float = _SIGMA_DEFAULT,
    ) -> None:
        if range_type not in ("bipolar", "unipolar"):
            raise ValueError("range_type debe ser 'bipolar' o 'unipolar'")
        self.range_type = range_type
        self.temperature = float(temperature)
        self.lambda_social = float(lambda_social)
        self.sigma = float(sigma)
        self._min = -1.0 if range_type == "bipolar" else 0.0
        self._max = 1.0

    # ── Energía individual ──────────────────────────────────────────────

    def _energy_point(
        self,
        x: float,
        attractors: list[dict],
        repellers: list[dict],
    ) -> float:
        """Calcula la energía potencial en un punto escalar x."""
        E = 0.0
        sigma2 = self.sigma ** 2
        for att in attractors:
            E -= att["strength"] * np.exp(-((x - att["position"]) ** 2) / (2 * sigma2))
        for rep in repellers:
            E += rep["strength"] * np.exp(-((x - rep["position"]) ** 2) / (2 * sigma2))
        return E

    def energy_global(
        self,
        opinions: np.ndarray,
        attractors: list[dict],
        repellers: Optional[list[dict]] = None,
    ) -> np.ndarray:
        """
        Calcula la energía de cada agente.

        Returns
        -------
        np.ndarray
            Vector de energías de forma (n,).
        """
        repellers = repellers or []
        return np.array([
            self._energy_point(x, attractors, repellers)
            for x in opinions
        ])

    # ── Gradiente del campo de energía ─────────────────────────────────

    def _gradient(
        self,
        opinions: np.ndarray,
        attractors: list[dict],
        repellers: list[dict],
    ) -> np.ndarray:
        """∇E vectorizado sobre todos los agentes."""
        sigma2 = self.sigma ** 2
        grad = np.zeros_like(opinions)
        for att in attractors:
            diff = opinions - att["position"]
            grad -= att["strength"] * (-diff / sigma2) * np.exp(-(diff ** 2) / (2 * sigma2))
        for rep in repellers:
            diff = opinions - rep["position"]
            grad += rep["strength"] * (-diff / sigma2) * np.exp(-(diff ** 2) / (2 * sigma2))
        return grad

    # ── Paso de integración Langevin ────────────────────────────────────

    def step(
        self,
        opinions: np.ndarray,
        adj: np.ndarray,
        attractors: list[dict],
        repellers: Optional[list[dict]] = None,
        eta: float = 0.01,
        rng: Optional[np.random.Generator] = None,
    ) -> np.ndarray:
        """
        Ejecuta un paso de integración estocástica de Langevin.

        x_{t+1} = x_t - η·∇E - η·λ·L·x + √(2ηT)·ε

        Parameters
        ----------
        opinions : np.ndarray
            Vector de opiniones actuales, forma (n,).
        adj : np.ndarray
            Matriz de adyacencia (n, n).
        attractors : list[dict]
            Lista de atractores con ``position`` y ``strength``.
        repellers : list[dict], optional
            Lista de repulsores con ``position`` y ``strength``.
        eta : float
            Tamaño del paso de integración.
        rng : np.random.Generator, optional
            Generador de números aleatorios. Si None, usa numpy global.

        Returns
        -------
        np.ndarray
            Nuevas opiniones recortadas al rango válido.
        """
        repellers = repellers or []
        if rng is None:
            rng = np.random.default_rng()

        # 1. Gradiente del paisaje energético
        grad = self._gradient(opinions, attractors, repellers)

        # 2. Presión social Laplaciana (empuja hacia el promedio de vecinos)
        L = _laplacian(adj)
        social_force = -self.lambda_social * (L @ opinions)

        # 3. Ruido térmico (libre albedrío)
        noise_scale = np.sqrt(2.0 * eta * self.temperature)
        noise = rng.standard_normal(len(opinions)) * noise_scale

        # 4. Integración
        new_opinions = opinions - eta * grad + eta * social_force + noise

        # 5. Recortar al rango válido
        return np.clip(new_opinions, self._min, self._max)

    # ── Métricas del sistema ────────────────────────────────────────────

    def system_metrics(
        self,
        opinions: np.ndarray,
        adj: np.ndarray,
        attractors: list[dict],
        repellers: Optional[list[dict]] = None,
    ) -> dict:
        """
        Calcula métricas de estado del sistema.

        Returns
        -------
        dict con claves:
            - ``tension_total``: energía media del sistema.
            - ``polarizacion``: desviación estándar de las opiniones.
            - ``disonancia_red``: diferencia cuadrática media entre vecinos.
            - ``convergencia``: 1 - (std normalizada); medida de cohesión.
        """
        repellers = repellers or []
        energies = self.energy_global(opinions, attractors, repellers)
        tension_total = float(np.mean(energies))
        polarizacion = float(np.std(opinions))

        # Disonancia de red: promedio de |x_i - x_j|² para pares enlazados
        rows, cols = np.where(adj > 0)
        if len(rows) > 0:
            diffs = opinions[rows] - opinions[cols]
            disonancia_red = float(np.mean(diffs ** 2))
        else:
            disonancia_red = 0.0

        # Convergencia: 1 cuando todos están de acuerdo, 0 cuando polarización máxima
        rango = self._max - self._min
        convergencia = float(1.0 - polarizacion / (rango / 2.0 + 1e-9))
        convergencia = float(np.clip(convergencia, 0.0, 1.0))

        return {
            "tension_total": tension_total,
            "polarizacion": polarizacion,
            "disonancia_red": disonancia_red,
            "convergencia": convergencia,
        }
