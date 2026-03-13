from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from scipy.io import loadmat


def _pick_first_matrix(data: dict[str, Any], candidates: list[str]) -> np.ndarray:
    for name in candidates:
        value = data.get(name)
        if isinstance(value, np.ndarray):
            return np.asarray(value, dtype=float)
    raise KeyError(f"None of the expected variables were found: {candidates}")


def load_mat_database(path: str | Path) -> np.ndarray:
    """Load the database matrix from a MATLAB .mat file.

    Expected variable names:
    - database
    - DB
    """
    mat = loadmat(Path(path), squeeze_me=False, struct_as_record=False)
    db = _pick_first_matrix(mat, ["database", "DB"])
    return np.asarray(db, dtype=float)


def load_mat_range(path: str | Path) -> np.ndarray:
    """Load the variable range matrix [M x 2] from a MATLAB .mat file.

    Expected variable names:
    - range_design
    - Urange
    """
    mat = loadmat(Path(path), squeeze_me=False, struct_as_record=False)
    urange = _pick_first_matrix(mat, ["range_design", "Urange"])
    urange = np.asarray(urange, dtype=float)

    if urange.ndim != 2 or urange.shape[1] != 2:
        raise ValueError(
            f"Expected a [M x 2] range matrix, got shape {urange.shape}"
        )
    return urange
