"""
Tests for FASE 2.3 — calcular_fiedler() and alerta_fragmentacion().
Verifies:
  1. λ₂ = 0 for disconnected graphs (fragmentation already occurred).
  2. λ₂ > 0 for connected graphs.
  3. Higher connectivity → higher λ₂.
  4. alerta_fragmentacion() triggers correctly near threshold.
  5. Trivial graph edge cases (N=1, N=2).
"""

import numpy as np
import pytest

from simulator import alerta_fragmentacion, calcular_fiedler


class TestCalcularFiedler:

    def test_disconnected_graph_returns_zero(self):
        """Two isolated components → λ₂ = 0."""
        # Block-diagonal: two 2-node cliques with no inter-connections
        W = np.array([
            [0, 1, 0, 0],
            [1, 0, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0],
        ], dtype=float)
        fiedler = calcular_fiedler(W)
        assert fiedler == pytest.approx(0.0, abs=1e-8), (
            f"Disconnected graph should have λ₂=0, got {fiedler}"
        )

    def test_connected_path_graph_positive(self):
        """Path graph (1-2-3-4) is connected → λ₂ > 0."""
        W = np.array([
            [0, 1, 0, 0],
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0],
        ], dtype=float)
        fiedler = calcular_fiedler(W)
        assert fiedler > 0.0, f"Connected path graph should have λ₂>0, got {fiedler}"

    def test_complete_graph_has_higher_fiedler(self):
        """K₄ (fully connected) should have higher λ₂ than path graph."""
        # Path graph K4 vs full K4
        W_path = np.array([
            [0, 1, 0, 0],
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0],
        ], dtype=float)
        W_complete = np.ones((4, 4)) - np.eye(4)
        fiedler_path     = calcular_fiedler(W_path)
        fiedler_complete = calcular_fiedler(W_complete)
        assert fiedler_complete > fiedler_path, (
            f"Complete graph (λ₂={fiedler_complete:.4f}) should exceed "
            f"path graph (λ₂={fiedler_path:.4f})"
        )

    def test_single_node_returns_zero(self):
        """Trivial case: 1×1 matrix → λ₂ = 0."""
        W = np.array([[0.0]])
        assert calcular_fiedler(W) == 0.0

    def test_two_node_connected(self):
        """Two nodes connected by edge → λ₂ = 2 (eigenvalues of L are [0, 2])."""
        W = np.array([[0, 1], [1, 0]], dtype=float)
        fiedler = calcular_fiedler(W)
        assert fiedler == pytest.approx(2.0, abs=1e-8)

    def test_two_node_disconnected(self):
        """Two isolated nodes → λ₂ = 0."""
        W = np.zeros((2, 2))
        assert calcular_fiedler(W) == pytest.approx(0.0, abs=1e-8)

    def test_weighted_graph_fiedler_positive(self):
        """Weighted symmetric matrix → λ₂ > 0 if connected."""
        W = np.array([
            [0.0, 0.8, 0.3],
            [0.8, 0.0, 0.5],
            [0.3, 0.5, 0.0],
        ])
        assert calcular_fiedler(W) > 0.0

    def test_fiedler_symmetric_invariant(self):
        """Transposing a symmetric W should not change λ₂."""
        W = np.array([
            [0, 2, 1, 0],
            [2, 0, 3, 1],
            [1, 3, 0, 4],
            [0, 1, 4, 0],
        ], dtype=float)
        assert calcular_fiedler(W) == pytest.approx(calcular_fiedler(W.T), abs=1e-10)


class TestAlertaFragmentacion:

    def test_disconnected_triggers_alert(self):
        """Disconnected graph → fragmentacion_inminente = True."""
        W = np.block([
            [np.ones((3, 3)) - np.eye(3), np.zeros((3, 3))],
            [np.zeros((3, 3)), np.ones((3, 3)) - np.eye(3)],
        ])
        result = alerta_fragmentacion(W, umbral=0.05)
        assert result["fragmentacion_inminente"] is True
        assert result["nivel_riesgo"] == "alto"

    def test_connected_no_alert(self):
        """Fully connected graph → no fragmentation alert."""
        W = np.ones((5, 5)) - np.eye(5)
        result = alerta_fragmentacion(W, umbral=0.05)
        assert result["fragmentacion_inminente"] is False

    def test_result_has_required_keys(self):
        """Result dict must have fiedler, fragmentacion_inminente, nivel_riesgo."""
        W = np.array([[0, 1], [1, 0]], dtype=float)
        result = alerta_fragmentacion(W)
        assert "fiedler" in result
        assert "fragmentacion_inminente" in result
        assert "nivel_riesgo" in result

    def test_fiedler_value_matches_standalone(self):
        """fiedler field must match calcular_fiedler() standalone output."""
        W = np.array([
            [0, 1, 1],
            [1, 0, 1],
            [1, 1, 0],
        ], dtype=float)
        standalone = calcular_fiedler(W)
        alert_val   = alerta_fragmentacion(W)["fiedler"]
        assert alert_val == pytest.approx(standalone, rel=1e-5)
