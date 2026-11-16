"""Snapshot fitting and projection from repeatable observation row readers."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from numbers import Integral, Real
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .model import _choose_nconf
from .snapshot import _eigensystem, _signs, _solver_options

Array = NDArray[np.float64]
RowReader = Callable[[int, int], Array]
Weights = Array | RowReader
ModeWriter = Callable[[int, int, Array], None]


def _shape(shape: Sequence[int]) -> tuple[int, int]:
    if len(shape) != 2 or any(isinstance(v, bool) or not isinstance(v, Integral) for v in shape):
        raise ValueError("shape must contain integer observation and sample counts")
    rows, samples = int(shape[0]), int(shape[1])
    if rows < 1 or samples < 2:
        raise ValueError("Streaming fit requires at least one observation and two samples")
    return rows, samples


def _read(reader: RowReader, start: int, stop: int, samples: int) -> Array:
    block = reader(start, stop)
    if np.iscomplexobj(block):
        raise ValueError("Observation blocks must be real")
    block = np.asarray(block, dtype=float)
    if block.shape != (stop - start, samples):
        raise ValueError(
            f"Reader returned {block.shape}; expected {(stop - start, samples)}"
        )
    if not np.all(np.isfinite(block)):
        raise ValueError("Observation blocks must be finite")
    return block


def _weight_reader(weights: Weights, rows: int) -> RowReader:
    if callable(weights):
        provider = weights
    else:
        if np.iscomplexobj(weights):
            raise ValueError("Streaming weights must be real")
        vector = np.asarray(weights, dtype=float)
        if vector.ndim == 2 and 1 in vector.shape:
            vector = vector.reshape(-1)
        if vector.ndim != 1 or vector.size != rows:
            raise ValueError("Streaming weights must contain one value per observation")
        provider = lambda start, stop: vector[start:stop]

    def read_weights(start: int, stop: int) -> Array:
        block = provider(start, stop)
        if np.iscomplexobj(block):
            raise ValueError("Streaming weights must be real")
        block = np.asarray(block, dtype=float)
        if block.ndim == 2 and 1 in block.shape:
            block = block.reshape(-1)
        if block.ndim != 1 or block.size != stop - start:
            raise ValueError("Weight reader returned an incorrect number of rows")
        if not np.all(np.isfinite(block)) or np.any(block < 0):
            raise ValueError("Streaming weights must be finite and nonnegative")
        return block

    return read_weights


def _center(block: Array) -> tuple[Array, Array, Array]:
    """Center through baseline differences, as in the regular case workflow."""
    baseline = block[:, [0]]
    delta = block - baseline
    delta_mean = np.mean(delta, axis=1, keepdims=True)
    return delta - delta_mean, baseline, delta_mean


def fit_streaming(
    reader: RowReader,
    shape: Sequence[int],
    weights: Weights,
    native: Array,
    options: dict[str, Any] | None = None,
    *,
    ci: float = 0.95,
    mode_writer: ModeWriter | None = None,
) -> dict[str, Any]:
    """Fit a compact native-variable embedding without storing observations.

    ``reader(start, stop)`` returns raw observation rows with shape
    ``(stop-start, samples)`` using zero-based, half-open indices. It must
    return the same construction data on every pass. ``weights`` is either
    a vector or a reader with the same row convention. The global metric is
    fixed before fitting; any source-variance normalization is performed in
    a preliminary pass, never separately for each storage block.

    ``native`` contains the already prepared native variables, one design
    per column. Their units and any normalization remain the caller's choice.
    The returned model stores only selected sample coefficients and native
    modes, plus the resolved spectrum and diagnostics. It contains neither
    the observation matrix nor its modes or row means. ``mode_writer`` can
    receive observation modes in a second pass without accumulating them.
    """
    rows, samples = _shape(shape)
    if not callable(reader):
        raise ValueError("reader must be a callable observation row reader")
    if mode_writer is not None and not callable(mode_writer):
        raise ValueError("mode_writer must be callable")
    if np.iscomplexobj(native):
        raise ValueError("Native snapshots must be real")
    native = np.asarray(native, dtype=float)
    if native.ndim != 2 or native.shape[0] < 1 or native.shape[1] != samples:
        raise ValueError("Native snapshots must have one row per variable and one column per sample")
    if not np.all(np.isfinite(native)):
        raise ValueError("Native snapshots must be finite")
    if isinstance(ci, bool) or not isinstance(ci, Real) or not np.isfinite(ci) or not 0 < ci <= 1:
        raise ValueError("CI must lie in (0, 1]")
    settings = _solver_options(samples, options)
    block_rows = settings["block_rows"]
    read_weights = _weight_reader(weights, rows)
    root_samples = np.sqrt(float(samples))
    gram = np.zeros((samples, samples), dtype=float)
    for start in range(0, rows, block_rows):
        stop = min(start + block_rows, rows)
        raw = _read(reader, start, stop, samples)
        centered, _, _ = _center(raw)
        weighted = np.sqrt(read_weights(start, stop))[:, None] * (centered / root_samples)
        gram += weighted.T @ weighted

    eigenvalues, vectors, info = _eigensystem(gram, samples, settings, "snapshot")
    nconf = _choose_nconf(
        eigenvalues, float(ci), info["total_variance"],
        info["cluster_rtol"], info["eigenvalue_threshold"],
    )
    sample_vectors = vectors[:, :nconf].copy()
    sample_vectors *= _signs(sample_vectors)
    scale = root_samples * np.sqrt(eigenvalues[:nconf])
    lifting = sample_vectors / scale[None, :]
    native_centered, native_baseline, native_delta_mean = _center(native)
    native_mean = native_baseline + native_delta_mean
    native_modes = native_centered @ lifting
    coordinates = sample_vectors * scale[None, :]
    if not np.all(np.isfinite(native_modes)) or not np.all(np.isfinite(coordinates)):
        raise ValueError("Streaming native-mode recovery produced nonfinite values")
    achieved_ci = float(np.sum(eigenvalues[:nconf]) / info["total_variance"])
    info.update(
        achieved_ci=achieved_ci,
        resolved_variance_fraction=float(np.sum(eigenvalues) / info["total_variance"]),
        ci_met=bool(achieved_ci + 10 * np.finfo(float).eps >= ci),
        observation_passes=1 + int(mode_writer is not None),
    )
    model = {
        "shape": (rows, samples),
        "eigenvalues": eigenvalues,
        "sample_vectors": sample_vectors,
        "lifting": lifting,
        "coordinates": coordinates,
        "native_mean": native_mean,
        "native_modes": native_modes,
        "nconf": nconf,
        "info": info,
    }
    if mode_writer is not None:
        for start in range(0, rows, block_rows):
            stop = min(start + block_rows, rows)
            raw = _read(reader, start, stop, samples)
            centered, _, _ = _center(raw)
            modes = centered @ lifting
            if not np.all(np.isfinite(modes)):
                raise ValueError("Streaming observation-mode recovery produced nonfinite values")
            mode_writer(start, stop, modes)
    return model


def transform_streaming(
    model: dict[str, Any],
    training_reader: RowReader,
    query_reader: RowReader,
    query_samples: int,
    weights: Weights,
) -> Array:
    """Encode query observations by cross-Gram products using training means.

    The construction reader and metric must be identical to those used by
    :func:`fit_streaming`. Query rows must use the same ordering and units.
    The result has one query per row and ``model['nconf']`` columns. No query
    mean is subtracted: centering always uses the construction observations.
    """
    rows, samples = _shape(model["shape"])
    if isinstance(query_samples, bool) or not isinstance(query_samples, Integral) or query_samples < 1:
        raise ValueError("query_samples must be a positive integer")
    if not callable(training_reader) or not callable(query_reader):
        raise ValueError("Training and query readers must be callable")
    read_weights = _weight_reader(weights, rows)
    block_rows = int(model["info"]["block_rows"])
    cross_gram = np.zeros((query_samples, samples), dtype=float)
    root_samples = np.sqrt(float(samples))
    for start in range(0, rows, block_rows):
        stop = min(start + block_rows, rows)
        training = _read(training_reader, start, stop, samples)
        query = _read(query_reader, start, stop, query_samples)
        centered, baseline, delta_mean = _center(training)
        root_w = np.sqrt(read_weights(start, stop))[:, None]
        weighted_training = root_w * (centered / root_samples)
        weighted_query = root_w * (((query - baseline) - delta_mean) / root_samples)
        cross_gram += weighted_query.T @ weighted_training
    eigenvalues = model["eigenvalues"][: model["nconf"]]
    coordinates = cross_gram @ (
        model["sample_vectors"] * (root_samples / np.sqrt(eigenvalues))[None, :]
    )
    if not np.all(np.isfinite(coordinates)):
        raise ValueError("Streaming query projection produced nonfinite values")
    return coordinates


def backmap_streaming(model: dict[str, Any], coordinates: Array) -> Array:
    """Return native variables as variables-by-queries in their supplied units."""
    if np.iscomplexobj(coordinates):
        raise ValueError("Coordinates must be real")
    coordinates = np.atleast_2d(np.asarray(coordinates, dtype=float))
    if coordinates.ndim != 2 or coordinates.shape[1] != model["nconf"]:
        raise ValueError(f"Coordinates must have {model['nconf']} columns")
    if not np.all(np.isfinite(coordinates)):
        raise ValueError("Coordinates must be finite")
    native = model["native_mean"] + model["native_modes"] @ coordinates.T
    if not np.all(np.isfinite(native)):
        raise ValueError("Streaming backmapping produced nonfinite values")
    return native
