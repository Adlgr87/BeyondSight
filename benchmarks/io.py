"""
benchmarks/io.py — Load and validate PVU-BS cases from disk.

Each case directory must contain:
  - meta.json
  - timeseries.csv
  - interventions.json
  - network.csv
"""
from __future__ import annotations

import json
import os
from typing import Any

import numpy as np

try:
    import pandas as pd
    _PANDAS_AVAILABLE = True
except ImportError:
    _PANDAS_AVAILABLE = False


_REQUIRED_META_FIELDS = {
    "case_id", "description", "source", "domain",
    "language", "date_range", "granularity", "opinion_range",
    "license", "is_synthetic",
}
_REQUIRED_TS_COLUMNS = {"t", "date", "polarization"}
_REQUIRED_NET_COLUMNS = {"node_a", "node_b", "weight"}


class PVUCase:
    """Container for a loaded PVU-BS case."""

    def __init__(
        self,
        case_id: str,
        meta: dict[str, Any],
        timeseries: "pd.DataFrame",
        interventions: list[dict[str, Any]],
        network: "pd.DataFrame",
        path: str,
    ) -> None:
        self.case_id = case_id
        self.meta = meta
        self.timeseries = timeseries
        self.interventions = interventions
        self.network = network
        self.path = path

    def __repr__(self) -> str:
        n = len(self.timeseries) if self.timeseries is not None else "?"
        return f"<PVUCase id={self.case_id!r} steps={n}>"


def _read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _read_csv_numpy(path: str) -> tuple[list[str], list[list[str]]]:
    """Read a CSV file without pandas and return (headers, rows)."""
    rows: list[list[str]] = []
    with open(path, "r", encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    if not lines:
        return [], []
    headers = [h.strip() for h in lines[0].split(",")]
    for line in lines[1:]:
        if line.strip():
            rows.append([c.strip() for c in line.split(",")])
    return headers, rows


def _validate_meta(meta: dict[str, Any], case_id: str) -> None:
    missing = _REQUIRED_META_FIELDS - set(meta.keys())
    if missing:
        raise ValueError(f"[{case_id}] meta.json missing required fields: {missing}")


def _validate_timeseries_pandas(df: "pd.DataFrame", case_id: str) -> None:
    import pandas as pd  # noqa: F401
    missing = _REQUIRED_TS_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"[{case_id}] timeseries.csv missing columns: {missing}")
    for col in ("t", "date", "polarization"):
        if df[col].isnull().any():
            raise ValueError(f"[{case_id}] timeseries.csv column '{col}' has NaN values")
    pol = df["polarization"].astype(float)
    if (pol < 0).any() or (pol > 1).any():
        raise ValueError(f"[{case_id}] timeseries.csv 'polarization' values must be in [0, 1]")


def _validate_timeseries_numpy(headers: list[str], rows: list[list[str]], case_id: str) -> None:
    missing = _REQUIRED_TS_COLUMNS - set(headers)
    if missing:
        raise ValueError(f"[{case_id}] timeseries.csv missing columns: {missing}")
    pol_idx = headers.index("polarization")
    for i, row in enumerate(rows):
        if not row:
            continue
        try:
            val = float(row[pol_idx])
        except (ValueError, IndexError):
            raise ValueError(f"[{case_id}] timeseries.csv row {i+1} has invalid polarization value")
        if val < 0 or val > 1:
            raise ValueError(
                f"[{case_id}] timeseries.csv row {i+1} polarization={val} outside [0,1]"
            )


def _validate_network_columns(columns: set[str], case_id: str) -> None:
    missing = _REQUIRED_NET_COLUMNS - columns
    if missing:
        raise ValueError(f"[{case_id}] network.csv missing columns: {missing}")


def load_case(case_dir: str) -> PVUCase:
    """Load a single PVU-BS case from *case_dir*.

    Parameters
    ----------
    case_dir:
        Path to the case directory (e.g. ``datasets/pvu_cases/sample_case_001``).

    Returns
    -------
    PVUCase
        Validated case object.

    Raises
    ------
    FileNotFoundError
        If a required file is missing.
    ValueError
        If schema validation fails.
    """
    case_id = os.path.basename(os.path.normpath(case_dir))

    # Check required files
    for fname in ("meta.json", "timeseries.csv", "interventions.json", "network.csv"):
        fpath = os.path.join(case_dir, fname)
        if not os.path.isfile(fpath):
            raise FileNotFoundError(f"[{case_id}] Required file not found: {fpath}")

    # Load meta
    meta = _read_json(os.path.join(case_dir, "meta.json"))
    _validate_meta(meta, case_id)
    case_id_from_meta = meta.get("case_id", case_id)

    # Load timeseries
    ts_path = os.path.join(case_dir, "timeseries.csv")
    if _PANDAS_AVAILABLE:
        import pandas as pd
        ts_df = pd.read_csv(ts_path)
        _validate_timeseries_pandas(ts_df, case_id_from_meta)
    else:
        headers, rows = _read_csv_numpy(ts_path)
        _validate_timeseries_numpy(headers, rows, case_id_from_meta)
        # Build a minimal dict-of-arrays representation wrapped in a stub
        ts_df = _build_ts_stub(headers, rows)

    # Load interventions
    interventions = _read_json(os.path.join(case_dir, "interventions.json"))
    if not isinstance(interventions, list):
        raise ValueError(f"[{case_id}] interventions.json must be a JSON array")

    # Load network
    net_path = os.path.join(case_dir, "network.csv")
    if _PANDAS_AVAILABLE:
        import pandas as pd
        net_df = pd.read_csv(net_path)
        _validate_network_columns(set(net_df.columns), case_id_from_meta)
    else:
        net_headers, net_rows = _read_csv_numpy(net_path)
        _validate_network_columns(set(net_headers), case_id_from_meta)
        net_df = _build_net_stub(net_headers, net_rows)

    return PVUCase(
        case_id=case_id_from_meta,
        meta=meta,
        timeseries=ts_df,
        interventions=interventions,
        network=net_df,
        path=case_dir,
    )


def load_cases(cases_dir: str) -> list[PVUCase]:
    """Load all cases from *cases_dir*.

    Subdirectories that do not contain ``meta.json`` are skipped with a warning.
    """
    cases: list[PVUCase] = []
    try:
        entries = sorted(os.listdir(cases_dir))
    except FileNotFoundError:
        raise FileNotFoundError(f"Cases directory not found: {cases_dir}")

    for entry in entries:
        entry_path = os.path.join(cases_dir, entry)
        if not os.path.isdir(entry_path):
            continue
        if not os.path.isfile(os.path.join(entry_path, "meta.json")):
            print(f"[io] Skipping {entry!r}: no meta.json found.")
            continue
        try:
            case = load_case(entry_path)
            cases.append(case)
        except (FileNotFoundError, ValueError) as exc:
            print(f"[io] WARNING: could not load case {entry!r}: {exc}")

    if not cases:
        raise ValueError(f"No valid PVU cases found in {cases_dir!r}")
    return cases


# ---------------------------------------------------------------------------
# Minimal stub objects for when pandas is not installed
# ---------------------------------------------------------------------------

class _ArrayFrame:
    """Minimal DataFrame-like backed by numpy arrays for when pandas is absent."""

    def __init__(self, data: dict[str, np.ndarray]) -> None:
        self._data = data
        self.columns = list(data.keys())

    def __getitem__(self, key: str) -> np.ndarray:
        return self._data[key]

    def __len__(self) -> int:
        if self._data:
            return len(next(iter(self._data.values())))
        return 0

    def isnull(self) -> "_NullChecker":
        return _NullChecker(self)


class _NullChecker:
    def __init__(self, frame: _ArrayFrame) -> None:
        self._frame = frame

    def any(self) -> bool:
        for arr in self._frame._data.values():
            if any(v is None or (isinstance(v, float) and np.isnan(v)) for v in arr):
                return True
        return False


def _build_ts_stub(headers: list[str], rows: list[list[str]]) -> _ArrayFrame:
    data: dict[str, np.ndarray] = {}
    for i, col in enumerate(headers):
        vals = []
        for row in rows:
            if i < len(row):
                raw = row[i]
                if col == "t":
                    vals.append(int(raw) if raw else 0)
                elif col == "polarization":
                    vals.append(float(raw) if raw else float("nan"))
                else:
                    vals.append(raw)
            else:
                vals.append(None)
        data[col] = np.array(vals) if col not in ("t", "polarization", "date") else np.array(vals)
    return _ArrayFrame(data)


def _build_net_stub(headers: list[str], rows: list[list[str]]) -> _ArrayFrame:
    data: dict[str, list] = {h: [] for h in headers}
    for row in rows:
        for i, h in enumerate(headers):
            data[h].append(row[i] if i < len(row) else None)
    return _ArrayFrame({k: np.array(v) for k, v in data.items()})
