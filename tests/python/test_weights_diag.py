"""Check metric normalization and the public dense compatibility interfaces."""
from pathlib import Path

import numpy as np
import pytest

from pme_toolkit.config_loader import load_config
from pme_toolkit.io import load_mat_database, load_mat_range
from pme_toolkit.model import fit_pme
from pme_toolkit.weights import build_wc, build_wf, build_weights, build_weights_diag


@pytest.mark.parametrize("mode", ["pme", "pi", "pd"])
def test_information_weights_match_known_source_variances(mode):
    # This sequence has population variance one. The source variances are
    # therefore known from the integer row amplitudes, independently of
    # either weight interface.
    sequence = np.array([[-1.0, 1.0, -1.0, 1.0]])
    geometry = np.array([[2.0], [1.0]]) * sequence
    native = 3.0 * sequence
    fields = np.array([[1.0], [2.0], [3.0], [4.0]]) * sequence
    scalars = np.array([[2.0], [3.0], [0.0]]) * sequence
    layout = {
        "D": {"nRows": 2},
        "F": {"items": [{"nRows": 4, "nCond": 2}]},
        "C": {"items": [{"nCond": 2}, {"nCond": 1}]},
    }
    blocks = {"F": fields, "C": scalars}
    field_weights = [1 / 5, 1 / 5, 1 / 25, 1 / 25]
    scalar_weights = [1 / 4, 1 / 9, 1 / np.finfo(float).eps]
    if mode == "pme":
        delta = np.vstack([geometry, native])
        expected = [1 / 5, 1 / 5, 0.0]
        ninfo = {"D": 1, "F": 0, "C": 0, "total": 1}
    elif mode == "pi":
        delta = np.vstack([geometry, native, fields, scalars])
        expected = [1 / 5, 1 / 5, 0.0] + field_weights + scalar_weights
        ninfo = {"D": 1, "F": 2, "C": 3, "total": 6}
    else:
        delta = np.vstack([native, fields, scalars])
        expected = [0.0] + field_weights + scalar_weights
        ninfo = {"D": 0, "F": 2, "C": 3, "total": 5}

    expected_stats = {
        "mode": mode, "sizes": {"D": 2, "U": 1, "F": 4, "C": 3},
        "ninfo": ninfo, "wU": 0.0, "varU": 9.0,
    }
    if mode != "pd":
        expected_stats.update(wD=1 / 5, varD=5.0)
    if mode == "pi":
        expected_stats["ptrU0"] = 2

    for builder in (build_weights_diag, build_weights):
        metric, stats = builder(delta, layout, {"mode": mode}, {"Mact": 1}, blocks)
        target = expected if builder is build_weights_diag else np.diag(expected)
        np.testing.assert_array_equal(metric, target)
        assert stats == expected_stats

    if mode != "pme":
        field_start = 3 if mode == "pi" else 1
        field_metric, field_count, scalar_start = build_wf(delta, field_start, layout, 4)
        scalar_metric, scalar_count = build_wc(delta, scalar_start, layout, 3)
        np.testing.assert_array_equal(field_metric, np.diag(field_weights))
        np.testing.assert_array_equal(scalar_metric, np.diag(scalar_weights))
        assert field_count == 2
        assert scalar_count == 3
        assert scalar_start == field_start + 4


@pytest.mark.parametrize("builder", [build_wf, build_wc])
@pytest.mark.parametrize("length", [0, 2])
def test_dense_component_interfaces_preserve_empty_and_fallback_blocks(builder, length):
    delta = np.array([[99.0, -99.0], [-1.0, 1.0], [-2.0, 2.0]])
    result = builder(delta, 1, {}, length)
    metric, count = result[:2]
    expected = np.diag([1 / 5, 1 / 5]) if length else np.zeros((0, 0))
    np.testing.assert_array_equal(metric, expected)
    assert count == (1 if length else 0)
    if builder is build_wf:
        assert result[2] == 1 + length


def test_fit_pme_glider_eigvals_unchanged():
    """Smoke test: the user-facing fit still produces sane eigenvalues
    after switching to the diagonal weight path."""
    repo_root = Path(__file__).resolve().parents[2]
    cfg = load_config(repo_root / "benchmarks" / "standard" / "pme" / "glider" / "case.json")
    db = load_mat_database(repo_root / "tests" / "data" / "glider_tiny.mat")
    urange = load_mat_range(repo_root / "tests" / "data" / "glider_range.mat")

    model = fit_pme(db, cfg, urange_full=urange)

    # w must be 1D now (diagonal storage)
    assert model.w.ndim == 1
    assert model.w.size == model.pc.shape[0]

    # eigenvalues monotone non-increasing and non-negative
    assert np.all(np.diff(model.eigvals_full) <= 1e-12)
    assert np.all(model.eigvals_full >= -1e-10)

    # transform on training DB (filtered) yields the same alpha as alpha_train
    alpha = model.transform_valid(db)
    np.testing.assert_allclose(alpha, model.alpha_train, rtol=1e-8, atol=1e-10)
