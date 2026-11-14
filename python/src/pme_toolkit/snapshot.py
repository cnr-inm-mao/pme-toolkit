"""Weighted snapshot eigendecomposition with complete native-mode recovery."""

from __future__ import annotations

from numbers import Real
from typing import Any

import numpy as np
from numpy.typing import NDArray

Array = NDArray[np.float64]


def _nonnegative_option(options: dict[str, Any], name: str, default: float) -> float:
    value = options.get(name, default)
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"snapshot.{name} must be a finite nonnegative number")
    value = float(value)
    if not np.isfinite(value) or value < 0:
        raise ValueError(f"snapshot.{name} must be a finite nonnegative number")
    return value


def snapshot_decompose(
    pc: Array, weights: Array, options: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Solve the weighted Gram problem for an already centered data matrix.

    ``pc`` has one sample per column. ``weights`` is a nonnegative row
    metric; zero-weight rows are included when lifting the complete modes.
    Only numerically resolved positive eigenvalues are lifted. Coordinates
    have shape ``(samples, numerical_rank)``.

    Row blocks limit temporary weighted storage; the input data and returned
    complete modes remain in memory. Weights are fixed across all blocks.
    """
    if np.iscomplexobj(pc) or np.iscomplexobj(weights):
        raise ValueError("Snapshot data and weights must be real")
    pc = np.asarray(pc, dtype=float)
    weights = np.asarray(weights, dtype=float)
    if pc.ndim != 2 or pc.shape[0] == 0 or pc.shape[1] < 2:
        raise ValueError("Snapshot data must have at least one row and two samples")
    if weights.ndim == 2 and 1 in weights.shape:
        weights = weights.reshape(-1)
    if weights.ndim != 1 or weights.size != pc.shape[0]:
        raise ValueError("Snapshot weights must contain one value per data row")
    if not np.all(np.isfinite(pc)):
        raise ValueError("Snapshot data must be finite")
    if not np.all(np.isfinite(weights)) or np.any(weights < 0):
        raise ValueError("Snapshot weights must be finite and nonnegative")
    if options is None:
        options = {}
    if not isinstance(options, dict):
        raise ValueError("snapshot must be an object of solver options")

    samples = pc.shape[1]
    eps = np.finfo(float).eps
    eig_rtol_requested = _nonnegative_option(options, "eig_rtol", samples * eps)
    eig_rtol = max(eig_rtol_requested, samples * eps)
    eig_atol = _nonnegative_option(options, "eig_atol", 0.0)
    cluster_rtol = _nonnegative_option(options, "cluster_rtol", 1e-10)
    block_rows_value = _nonnegative_option(options, "block_rows", 4096)
    if block_rows_value < 1 or not block_rows_value.is_integer():
        raise ValueError("snapshot.block_rows must be a positive integer")
    block_rows = int(block_rows_value)

    gram = np.zeros((samples, samples), dtype=float)
    for start in range(0, pc.shape[0], block_rows):
        block = pc[start : start + block_rows]
        w_block = weights[start : start + block_rows]
        gram += (block.T @ (w_block[:, None] * block)) / samples
    gram = 0.5 * gram + 0.5 * gram.T
    if not np.all(np.isfinite(gram)):
        raise ValueError("Weighted snapshot Gram matrix is not finite")

    total_variance = float(np.trace(gram))
    if not np.isfinite(total_variance):
        raise ValueError("Total weighted snapshot variance is not finite")
    raw_values, raw_vectors = np.linalg.eigh(gram)
    raw_values = raw_values[::-1]
    raw_vectors = raw_vectors[:, ::-1]
    spectral_scale = float(np.max(np.abs(raw_values)))
    negative_tolerance = 100 * samples * eps * spectral_scale
    if np.any(raw_values < -negative_tolerance):
        raise ValueError("Weighted snapshot Gram matrix has significant negative eigenvalues")

    threshold = max(eig_atol, eig_rtol * max(float(raw_values[0]), 0.0))
    resolved = raw_values > threshold
    if total_variance <= 0 or not np.any(resolved):
        raise ValueError("No resolved positive weighted variance; check observations and snapshot tolerances")
    eigenvalues = raw_values[resolved]
    sample_vectors = raw_vectors[:, resolved]

    # A common sign convention is convenient; repeated eigenspaces still
    # admit rotations and must be compared through their subspaces.
    pivots = np.argmax(np.abs(sample_vectors), axis=0)
    signs = np.where(sample_vectors[pivots, np.arange(eigenvalues.size)] < 0, -1.0, 1.0)
    sample_vectors = sample_vectors * signs
    scale = np.sqrt(float(samples)) * np.sqrt(eigenvalues)
    modes = pc @ (sample_vectors / scale[None, :])
    coordinates = sample_vectors * scale[None, :]
    if not np.all(np.isfinite(modes)) or not np.all(np.isfinite(coordinates)):
        raise ValueError("Snapshot mode lifting produced nonfinite values")

    return {
        "eigenvalues": eigenvalues,
        "modes": modes,
        "coordinates": coordinates,
        "sample_vectors": sample_vectors,
        "info": {
            "total_variance": total_variance,
            "numerical_rank": int(eigenvalues.size),
            "eig_rtol": eig_rtol,
            "eig_rtol_requested": eig_rtol_requested,
            "eig_atol": eig_atol,
            "eigenvalue_threshold": threshold,
            "cluster_rtol": cluster_rtol,
            "block_rows": block_rows,
        },
    }
