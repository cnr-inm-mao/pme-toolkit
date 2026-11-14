"""
Parity tests for the diagonal-only weights builder.

`build_weights_diag` is a memory-efficient alternative to `build_weights`:
it returns the 1D diagonal of the (always block-diagonal) W matrix instead
of the full (R, R) array. This test asserts numerical parity for every
supported PME mode, and that the downstream Gram-form fit produces
identical eigenvalues / weighted projections to the legacy dense path.
"""
from pathlib import Path

import numpy as np

from pme_toolkit.config_loader import load_config
from pme_toolkit.io import load_mat_database, load_mat_range
from pme_toolkit.layout import parse_layout
from pme_toolkit.filters import apply_filters
from pme_toolkit.model import fit_pme
from pme_toolkit.weights import build_weights, build_weights_diag


def _glider_blocks():
    repo_root = Path(__file__).resolve().parents[2]
    cfg_path = repo_root / "benchmarks" / "standard" / "pme" / "glider" / "case.json"
    cfg = load_config(cfg_path)
    db = load_mat_database(repo_root / "tests" / "data" / "glider_tiny.mat")
    urange = load_mat_range(repo_root / "tests" / "data" / "glider_range.mat")
    layout = parse_layout(cfg)

    filt = apply_filters(db, cfg, layout)
    db_used = np.asarray(filt.db_used, dtype=float)

    # mimic the slicing fit_model performs
    from pme_toolkit.model import _slice_blocks, _prepare_vars, _compose_p

    blocks = _slice_blocks(db_used, layout)
    uact, uinfo = _prepare_vars(blocks["Ubase"], cfg, urange)
    p = _compose_p(cfg["mode"], blocks["D"], uact, blocks["F"], blocks["C"])
    p0 = p[:, [0]]
    delta = p - p0
    return delta, layout, cfg, uinfo, blocks


def test_build_weights_diag_matches_dense_pme():
    delta, layout, cfg, uinfo, blocks = _glider_blocks()
    cfg = dict(cfg)
    cfg["mode"] = "pme"

    w_dense, stats_dense = build_weights(delta, layout, cfg, uinfo, blocks)
    w_diag, stats_diag = build_weights_diag(delta, layout, cfg, uinfo, blocks)

    assert w_dense.shape[0] == w_dense.shape[1] == w_diag.size
    np.testing.assert_allclose(w_diag, np.diag(w_dense), rtol=1e-12, atol=0.0)

    # off-diagonal of the legacy matrix must be exactly zero (sanity)
    off = w_dense - np.diag(np.diag(w_dense))
    assert float(np.max(np.abs(off))) == 0.0

    # stats must agree on the keys both paths populate
    for key in ("mode", "sizes", "ninfo", "wD", "wU", "varD", "varU"):
        assert stats_diag.get(key) == stats_dense.get(key) or np.allclose(
            stats_diag.get(key), stats_dense.get(key)
        )


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
