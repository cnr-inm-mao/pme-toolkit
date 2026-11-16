"""Direct, snapshot, and file-backed fits against independent factorizations."""

import numpy as np
import pytest

from pme_toolkit import (
    backmap_streaming, decompose, direct_decompose, fit_streaming,
    snapshot_decompose, transform_streaming,
)
from test_snapshot import _prescribed_problem


def _problem():
    rng = np.random.default_rng(2187)
    samples, queries, rows, variables = 18, 7, 53, 4
    mapping = rng.normal(size=(rows, variables))
    native = rng.normal(size=(variables, samples)) + 3.0
    query_native = rng.normal(size=(variables, queries)) + 6.0
    offset = rng.normal(size=(rows, 1)) * 100
    training = offset + mapping @ native
    query = offset + mapping @ query_native
    weights = np.linspace(0.3, 2.4, rows)
    return training, query, native, weights


@pytest.mark.parametrize("block_rows", [1, 11, 4096])
def test_file_backed_fit_and_query_projection_match_rectangular_svd(tmp_path, block_rows):
    training, query, native, weights = _problem()
    path = tmp_path / "observations.npy"
    np.save(path, training)
    stored = np.load(path, mmap_mode="r")
    requests, written = [], []

    def reader(start, stop):
        requests.append((start, stop))
        assert stop - start <= block_rows
        return stored[start:stop]

    def writer(start, stop, modes):
        written.append((start, stop, modes.copy()))

    model = fit_streaming(
        reader, training.shape, lambda start, stop: weights[start:stop], native,
        {"block_rows": block_rows}, ci=0.9, mode_writer=writer,
    )
    centered = training - training.mean(axis=1, keepdims=True)
    left, singular, right = np.linalg.svd(np.sqrt(weights)[:, None] * centered, full_matrices=False)
    reference_values = singular[:native.shape[0]] ** 2 / training.shape[1]
    np.testing.assert_allclose(model["eigenvalues"], reference_values, rtol=3e-13)
    n = int(np.searchsorted(np.cumsum(reference_values) / reference_values.sum(), 0.9)) + 1
    assert model["nconf"] == n
    assert model["info"]["observation_passes"] == 2
    assert len(requests) == 2 * ((training.shape[0] + block_rows - 1) // block_rows)
    modes = np.vstack([item[2] for item in written])
    # The model stores no array whose leading dimension is the observation count.
    assert not any(isinstance(value, np.ndarray) and value.shape[0] == training.shape[0]
                   for value in model.values())
    np.testing.assert_allclose(modes.T @ (weights[:, None] * modes), np.eye(n), atol=2e-13)
    np.testing.assert_allclose(modes @ model["coordinates"].T,
                               centered @ right[:n].T @ right[:n], atol=3e-13)
    native_centered = native - native.mean(axis=1, keepdims=True)
    np.testing.assert_allclose(
        backmap_streaming(model, model["coordinates"]),
        native.mean(axis=1, keepdims=True) + native_centered @ right[:n].T @ right[:n],
        atol=3e-13,
    )
    coordinates = transform_streaming(
        model, reader, lambda start, stop: query[start:stop], query.shape[1], weights,
    )
    expected = (query - training.mean(axis=1, keepdims=True)).T @ (weights[:, None] * modes)
    np.testing.assert_allclose(coordinates, expected, atol=5e-13)
    assert np.linalg.norm(coordinates.mean(axis=0)) > 1.0  # Queries are not recentered.
    reference_query = (query - training.mean(axis=1, keepdims=True)).T @ (
        np.sqrt(weights)[:, None] * left[:, :n]
    )
    native_reference_modes = native_centered @ (right[:n].T / singular[:n])
    np.testing.assert_allclose(
        backmap_streaming(model, coordinates),
        native.mean(axis=1, keepdims=True) + native_reference_modes @ reference_query.T,
        atol=3e-13,
    )


def test_streaming_retains_whole_cluster_and_excludes_native_null_direction():
    pc, weights, spectrum, sample, q = _prescribed_problem()
    reader = lambda start, stop: pc[start:stop]
    model = fit_streaming(reader, (q, pc.shape[1]), weights[:q], pc[q:],
                         {"block_rows": 13}, ci=4.5 / spectrum.sum())
    assert model["nconf"] == 3
    native = backmap_streaming(model, model["coordinates"])
    np.testing.assert_allclose(native, pc[q:] @ sample[:, :3] @ sample[:, :3].T, atol=4e-12)
    np.testing.assert_allclose(native[-1], 0.0, atol=4e-12)


def test_streaming_cutoff_reports_unattainable_variance_against_full_trace():
    pc, weights, _, _, q = _prescribed_problem([1.0, 0.1, 1e-4])
    with pytest.warns(RuntimeWarning):
        model = fit_streaming(lambda start, stop: pc[start:stop], (q, pc.shape[1]),
                             weights[:q], pc[q:], {"eig_atol": 0.01}, ci=1.0)
    assert model["info"]["total_variance"] == pytest.approx(1.1001)
    assert model["info"]["numerical_rank"] == 2
    assert not model["info"]["ci_met"]
    assert model["info"]["achieved_ci"] == pytest.approx(1.1 / 1.1001)


@pytest.mark.parametrize("solver", ["auto", "direct", "snapshot"])
def test_solver_selection_preserves_weighted_eigenspaces_and_native_backmap(solver):
    pc, weights, expected, _, q = _prescribed_problem()
    result = decompose(pc, weights, solver=solver)
    reference = snapshot_decompose(pc, weights)
    assert result["info"]["solver_requested"] == solver
    assert result["info"]["solver"] == ("snapshot" if solver == "auto" else solver)
    np.testing.assert_allclose(result["eigenvalues"], expected, rtol=1e-11)
    for n in (1, 3, 4, 6):
        left = np.sqrt(weights[:q])[:, None] * result["modes"][:q, :n]
        right = np.sqrt(weights[:q])[:, None] * reference["modes"][:q, :n]
        np.testing.assert_allclose(left @ left.T, right @ right.T, atol=3e-11)
        np.testing.assert_allclose(
            result["modes"][q:, :n] @ result["coordinates"][:, :n].T,
            reference["modes"][q:, :n] @ reference["coordinates"][:, :n].T,
            atol=3e-11,
        )


def test_auto_selects_direct_with_fewer_positive_weight_rows():
    rng = np.random.default_rng(199)
    pc = rng.normal(size=(30, 9))
    pc -= pc.mean(axis=1, keepdims=True)
    weights = np.zeros(30)
    weights[:3] = [1.0, 0.3, 2.1]
    result = decompose(pc, weights)
    assert result["info"]["solver"] == "direct"
    assert result["info"]["matrix_dimension"] == 3
    reference = snapshot_decompose(pc, weights)
    np.testing.assert_allclose(result["eigenvalues"], reference["eigenvalues"], atol=3e-14)
    np.testing.assert_allclose(result["modes"] @ result["coordinates"].T,
                               reference["modes"] @ reference["coordinates"].T, atol=1e-13)


def test_direct_large_finite_covariance_does_not_overflow_before_normalization():
    pc = np.array([[1e154, -1e154]])
    with np.errstate(over="raise", invalid="raise"):
        result = direct_decompose(pc, np.ones(1))
    np.testing.assert_allclose(result["eigenvalues"], [1e308], rtol=1e-14)
    np.testing.assert_allclose(result["modes"] @ result["coordinates"].T, pc, rtol=1e-14)


@pytest.mark.parametrize("bad_reader", [
    lambda start, stop: np.zeros((stop - start, 2)),
    lambda start, stop: np.full((stop - start, 4), np.nan),
    lambda start, stop: np.ones((stop - start, 4), dtype=complex) * 1j,
])
def test_invalid_observation_readers_are_rejected(bad_reader):
    with pytest.raises(ValueError):
        fit_streaming(bad_reader, (5, 4), np.ones(5), np.ones((2, 4)))


@pytest.mark.parametrize("weights", [
    np.ones(3), np.array([1.0, -1.0, 1.0, 1.0, 1.0]),
    lambda start, stop: np.ones(stop - start + 1),
    lambda start, stop: np.full(stop - start, np.inf),
])
def test_invalid_streaming_metrics_are_rejected(weights):
    reader = lambda start, stop: np.tile(np.arange(4), (stop - start, 1))
    with pytest.raises(ValueError):
        fit_streaming(reader, (5, 4), weights, np.ones((2, 4)))


@pytest.mark.parametrize("solver", ["legacy", None, 1])
def test_invalid_solver_is_rejected(solver):
    with pytest.raises(ValueError, match="solver"):
        decompose(np.array([[-1.0, 0.0, 1.0]]), np.ones(1), solver=solver)
