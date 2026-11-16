"""Weighted symmetric eigensolvers with complete native-mode recovery."""

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


def _validate_data(pc: Array, weights: Array) -> tuple[Array, Array]:
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
    return pc, weights


def _solver_options(samples: int, options: dict[str, Any] | None) -> dict[str, Any]:
    if options is None:
        options = {}
    if not isinstance(options, dict):
        raise ValueError("snapshot must be an object of solver options")

    eps = np.finfo(float).eps
    eig_rtol_requested = _nonnegative_option(options, "eig_rtol", samples * eps)
    eig_rtol = max(eig_rtol_requested, samples * eps)
    eig_atol = _nonnegative_option(options, "eig_atol", 0.0)
    cluster_rtol = _nonnegative_option(options, "cluster_rtol", 1e-10)
    block_rows_value = _nonnegative_option(options, "block_rows", 4096)
    if block_rows_value < 1 or not block_rows_value.is_integer():
        raise ValueError("snapshot.block_rows must be a positive integer")
    block_rows = int(block_rows_value)
    return {
        "eig_rtol": eig_rtol,
        "eig_rtol_requested": eig_rtol_requested,
        "eig_atol": eig_atol,
        "cluster_rtol": cluster_rtol,
        "block_rows": block_rows,
    }


def _eigensystem(
    matrix: Array, samples: int, options: dict[str, Any], solver: str
) -> tuple[Array, Array, dict[str, Any]]:
    """Resolve the positive spectrum using a common trace and rank policy."""
    matrix = 0.5 * matrix + 0.5 * matrix.T
    if not np.all(np.isfinite(matrix)):
        raise ValueError("Weighted covariance or Gram matrix is not finite")
    total_variance = float(np.trace(matrix))
    if not np.isfinite(total_variance):
        raise ValueError("Total weighted snapshot variance is not finite")
    if matrix.shape[0] == 0:
        raise ValueError("No resolved positive weighted variance; check observations and snapshot tolerances")
    raw_values, raw_vectors = np.linalg.eigh(matrix)
    raw_values = raw_values[::-1]
    raw_vectors = raw_vectors[:, ::-1]
    spectral_scale = float(np.max(np.abs(raw_values)))
    negative_tolerance = 100 * samples * np.finfo(float).eps * spectral_scale
    if np.any(raw_values < -negative_tolerance):
        raise ValueError("Weighted snapshot Gram matrix has significant negative eigenvalues")

    threshold = max(options["eig_atol"], options["eig_rtol"] * max(float(raw_values[0]), 0.0))
    resolved = raw_values > threshold
    if total_variance <= 0 or not np.any(resolved):
        raise ValueError("No resolved positive weighted variance; check observations and snapshot tolerances")
    info = dict(options)
    info.update(
        total_variance=total_variance,
        numerical_rank=int(np.count_nonzero(resolved)),
        eigenvalue_threshold=threshold,
        solver=solver,
        solver_requested=solver,
        matrix_dimension=int(matrix.shape[0]),
    )
    return raw_values[resolved], raw_vectors[:, resolved], info


def _signs(sample_vectors: Array) -> Array:
    # A common sign convention is convenient; repeated eigenspaces still
    # admit rotations and must be compared through their subspaces.
    pivots = np.argmax(np.abs(sample_vectors), axis=0)
    return np.where(sample_vectors[pivots, np.arange(sample_vectors.shape[1])] < 0, -1.0, 1.0)


def snapshot_decompose(
    pc: Array, weights: Array, options: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Solve the sample-space Gram problem for centered row-by-sample data.

    Zero-weight rows are included in the lifted modes. Only resolved positive
    modes are returned. The input and complete output modes remain in memory;
    use :func:`fit_streaming` for an out-of-core observation reader.
    """
    pc, weights = _validate_data(pc, weights)
    samples = pc.shape[1]
    settings = _solver_options(samples, options)
    block_rows = settings["block_rows"]
    gram = np.zeros((samples, samples), dtype=float)
    for start in range(0, pc.shape[0], block_rows):
        block = pc[start : start + block_rows]
        w_block = weights[start : start + block_rows]
        weighted = np.sqrt(w_block)[:, None] * (block / np.sqrt(float(samples)))
        gram += weighted.T @ weighted
    eigenvalues, sample_vectors, info = _eigensystem(gram, samples, settings, "snapshot")
    sample_vectors *= _signs(sample_vectors)
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
        "info": info,
    }


def direct_decompose(
    pc: Array, weights: Array, options: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Solve the symmetric covariance of the positive-weight observations.

    Native and other zero-weight rows are recovered using the paired sample
    coefficients. This formulation is economical when observations are fewer
    than construction samples. It uses the same rank cutoff as snapshot PME.
    """
    pc, weights = _validate_data(pc, weights)
    samples = pc.shape[1]
    settings = _solver_options(samples, options)
    active = weights > 0
    sqrt_w = np.sqrt(weights[active])
    weighted = sqrt_w[:, None] * (pc[active] / np.sqrt(float(samples)))
    eigenvalues, vectors, info = _eigensystem(
        weighted @ weighted.T, samples, settings, "direct"
    )
    sample_vectors = (weighted.T @ vectors) / np.sqrt(eigenvalues)[None, :]
    signs = _signs(sample_vectors)
    sample_vectors *= signs
    vectors *= signs
    scale = np.sqrt(float(samples)) * np.sqrt(eigenvalues)
    modes = np.empty((pc.shape[0], eigenvalues.size), dtype=float)
    modes[active] = vectors / sqrt_w[:, None]
    modes[~active] = pc[~active] @ (sample_vectors / scale[None, :])
    coordinates = sample_vectors * scale[None, :]
    if not np.all(np.isfinite(modes)) or not np.all(np.isfinite(coordinates)):
        raise ValueError("Direct mode recovery produced nonfinite values")
    return {
        "eigenvalues": eigenvalues,
        "modes": modes,
        "coordinates": coordinates,
        "sample_vectors": sample_vectors,
        "info": info,
    }


def decompose(
    pc: Array, weights: Array, options: dict[str, Any] | None = None,
    solver: str = "auto",
) -> dict[str, Any]:
    """Choose ``direct``, ``snapshot``, or the smaller symmetric problem.

    ``auto`` selects direct when the number of positive-weight rows is less
    than the sample count; otherwise it selects snapshot. No dense weight
    matrix or nonsymmetric augmented covariance is constructed.
    """
    if not isinstance(solver, str) or solver.lower() not in ("auto", "direct", "snapshot"):
        raise ValueError("solver must be 'auto', 'direct', or 'snapshot'")
    requested = solver.lower()
    pc, weights = _validate_data(pc, weights)
    selected = requested
    if requested == "auto":
        selected = "direct" if np.count_nonzero(weights) < pc.shape[1] else "snapshot"
    function = direct_decompose if selected == "direct" else snapshot_decompose
    result = function(pc, weights, options)
    result["info"]["solver_requested"] = requested
    return result
