"""
cache_manager.py — Gestor de caché para BeyondSight Architect

Arquitectura: Memoria RAM (ultra-rápido) + SQLite (persistente cross-session).
Compatible con: Streamlit, HF Spaces, Docker, serverless con volumen montado.

Flujo de lectura:
    1. Busca la clave en el dict en memoria (O(1)).
    2. Si no está, consulta SQLite y promueve al dict.
    3. Si SQLite falla, opera solo en memoria (modo degradado seguro).
"""

import hashlib
import json
import os
import sqlite3
from typing import Optional


class LandscapeCache:
    """
    Caché clave-valor para paisajes sociales generados por el LLM.

    Prioriza velocidad (dict en memoria) y persistencia (SQLite).
    Thread-safe para Streamlit (``check_same_thread=False``).

    Parameters
    ----------
    db_path : str, optional
        Ruta al archivo SQLite. Si ``None`` usa la variable de entorno
        ``CACHE_DB_PATH`` o el valor por defecto ``landscapes_cache.db``.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path: str = db_path or os.getenv(
            "CACHE_DB_PATH", "landscapes_cache.db"
        )
        self._memory: dict[str, dict] = {}
        self._init_db()

    # ── Inicialización ──────────────────────────────────────────────────

    def _init_db(self) -> None:
        """Crea la tabla SQLite si no existe. Falla silenciosamente."""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS landscapes (
                    key        TEXT PRIMARY KEY,
                    config     TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
            conn.close()
        except Exception as exc:
            print(
                f"[Cache] ⚠️  No se pudo inicializar SQLite: {exc}. "
                "Caché solo en memoria."
            )

    # ── Clave de hash ───────────────────────────────────────────────────

    def _key(self, goal: str) -> str:
        """Genera una clave MD5 de 12 caracteres (case-insensitive)."""
        return hashlib.md5(goal.lower().strip().encode()).hexdigest()[:12]

    # ── Operaciones públicas ────────────────────────────────────────────

    def get(self, goal: str) -> Optional[dict]:
        """
        Recupera la configuración asociada a ``goal``.

        Consulta primero la memoria RAM; si no existe, busca en SQLite
        y promueve el resultado a memoria.

        Returns
        -------
        dict | None
            La configuración almacenada, o ``None`` si no existe.
        """
        k = self._key(goal)

        # Hit en memoria
        if k in self._memory:
            return self._memory[k]

        # Buscar en SQLite
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cur = conn.execute(
                "SELECT config FROM landscapes WHERE key = ?", (k,)
            )
            row = cur.fetchone()
            conn.close()
            if row:
                cfg: dict = json.loads(row[0])
                self._memory[k] = cfg  # promover a memoria
                return cfg
        except Exception:
            pass

        return None

    def set(self, goal: str, config: dict) -> None:
        """
        Almacena ``config`` para ``goal`` en RAM y SQLite.

        Parameters
        ----------
        goal : str
            Objetivo/intención del usuario (se normaliza internamente).
        config : dict
            Configuración del paisaje energético.
        """
        k = self._key(goal)
        self._memory[k] = config

        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.execute(
                """
                INSERT OR REPLACE INTO landscapes (key, config)
                VALUES (?, ?)
                """,
                (k, json.dumps(config, ensure_ascii=False)),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass  # Memoria ya actualizada; SQLite es best-effort

    def clear(self) -> None:
        """Limpia toda la caché (RAM + SQLite)."""
        self._memory.clear()
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.execute("DELETE FROM landscapes")
            conn.commit()
            conn.close()
        except Exception:
            pass

    def __len__(self) -> int:
        """Número de entradas en la caché en memoria."""
        return len(self._memory)
