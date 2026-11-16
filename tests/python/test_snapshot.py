"""Numerical checks for snapshot PME and its native-variable backmap."""

import json
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest

from pme_toolkit.model import PmeModel, _choose_nconf, fit_model
from pme_toolkit.snapshot import snapshot_decompose
from pme_toolkit.weights import build_weights, build_weights_diag


FIXTURE = Path(__file__).resolve().parents[1] / "data" / "snapshot_parity.json"


def _prescribed_problem(spectrum=None):
    """Pair weighted observations with native data, including an unseen direction."""
    lam = np.asarray(
        [4.0, 1.0, 1.0, 0.1, 0.01, 0.001] if spectrum is None else spectrum,
        dtype=float,
    )
    q, s, m = 160, 48, 6
    rng = np.random.default_rng(20261020)
    sample = rng.normal(size=(s, lam.size + 1))
    sample -= sample.mean(axis=0)
    sample, _ = np.linalg.qr(sample, mode="reduced")
    y, _ = np.linalg.qr(rng.normal(size=(q, lam.size)), mode="reduced")
    w = np.linspace(0.2, 2.8, q)
    h = ((y / np.sqrt(w)[:, None]) * np.sqrt(s * lam)) @ sample[:, :-1].T
    native = rng.normal(size=(m, lam.size)) @ sample[:, :-1].T
    native = np.vstack([native, sample[:, -1]])
    pc = np.vstack([h, native])
    return pc, np.concatenate([w, np.zeros(m + 1)]), lam, sample, q


def _direct_reference(pc, weights):
    """Solve the observation covariance and recover paired native components."""
    active = weights > 0
    h = pc[active]
    w = weights[active]
    s = pc.shape[1]
    b = np.sqrt(w)[:, None] * h
    covariance = b @ b.T / s
    values, vectors = np.linalg.eigh(covariance)
    order = np.argsort(values)[::-1]
    values, vectors = values[order], vectors[:, order]
    keep = values > 1e-11 * values[0]
    values, vectors = values[keep], vectors[:, keep]
    z = vectors / np.sqrt(w)[:, None]
    scores = h.T @ (w[:, None] * z)
    complete = (pc @ scores) / (s * values)[None, :]
    return values, complete, scores


def _case(mode):
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    cfg = deepcopy(payload["cfg"])
    cfg["mode"] = mode
    return np.asarray(payload["db"]), cfg, np.asarray(payload["urange"])


def test_prescribed_spectrum_matches_direct_modes_and_native_backmap():
    pc, w, expected, sample, q = _prescribed_problem()
    result = snapshot_decompose(pc, w)
    lam, z, scores = result["eigenvalues"], result["modes"], result["coordinates"]
    lam_direct, z_direct, scores_direct = _direct_reference(pc, w)

    assert result["info"]["numerical_rank"] == expected.size
    assert z.shape == (pc.shape[0], expected.size)
    np.testing.assert_allclose(lam, expected, rtol=2e-11, atol=2e-14)
    np.testing.assert_allclose(lam, lam_direct, rtol=2e-11, atol=2e-14)
    np.testing.assert_allclose(z.T @ (w[:, None] * z), np.eye(expected.size), atol=2e-11)
    np.testing.assert_allclose(pc.T @ (w[:, None] * z), scores, atol=2e-11)
    residual = pc @ (pc.T @ (w[:, None] * z)) / pc.shape[1] - z * lam
    assert np.linalg.norm(residual) / np.linalg.norm(z * lam) < 2e-12

    # Complete clusters are compared as subspaces, independently of signs/rotations.
    for n in (1, 3, 4, 6):
        y = np.sqrt(w[:q])[:, None] * z[:q, :n]
        y_direct = np.sqrt(w[:q])[:, None] * z_direct[:q, :n]
        np.testing.assert_allclose(y @ y.T, y_direct @ y_direct.T, atol=2e-11)
        native = z[q:, :n] @ scores[:, :n].T
        native_direct = z_direct[q:, :n] @ scores_direct[:, :n].T
        np.testing.assert_allclose(native, native_direct, atol=3e-11)

    reconstructed = z[q:] @ scores.T
    expected_native = pc[q:] @ sample[:, :-1] @ sample[:, :-1].T
    np.testing.assert_allclose(reconstructed, expected_native, atol=3e-11)
    # A native direction orthogonal to all observations remains unrecoverable.
    np.testing.assert_allclose(reconstructed[-1], 0.0, atol=3e-11)
    assert np.linalg.norm(pc[-1] - reconstructed[-1]) > 0.99


@pytest.mark.parametrize("block_rows", [1, 7, 4096])
def test_row_blocks_preserve_the_fixed_metric(block_rows):
    pc, w, _, _, _ = _prescribed_problem()
    whole = snapshot_decompose(pc, w, {"block_rows": pc.shape[0]})
    blocked = snapshot_decompose(pc, w, {"block_rows": block_rows})
    np.testing.assert_allclose(blocked["eigenvalues"], whole["eigenvalues"], rtol=2e-11)
    np.testing.assert_allclose(
        blocked["modes"] @ blocked["coordinates"].T,
        whole["modes"] @ whole["coordinates"].T,
        atol=3e-11,
    )
    np.testing.assert_allclose(blocked["info"]["total_variance"], whole["info"]["total_variance"])


def test_cutoff_keeps_full_trace_for_retained_variance():
    pc, w, _, _, _ = _prescribed_problem([1.0, 0.1, 1e-4])
    result = snapshot_decompose(pc, w, {"eig_atol": 0.01, "eig_rtol": 0.0})
    lam, info = result["eigenvalues"], result["info"]
    np.testing.assert_allclose(lam, [1.0, 0.1], rtol=1e-12)
    assert info["numerical_rank"] == 2
    assert info["eigenvalue_threshold"] == 0.01
    assert info["total_variance"] == pytest.approx(1.1001)
    # Renormalizing the resolved spectrum would incorrectly choose only one mode.
    ci = 0.5 * (lam[0] / info["total_variance"] + lam[0] / lam.sum())
    assert _choose_nconf(lam, ci, total_variance=info["total_variance"]) == 2


def test_retention_includes_the_complete_repeated_cluster():
    values = np.array([4.0, 1.0, 1.0, 0.1, 0.01, 0.001])
    assert _choose_nconf(values, 4.5 / values.sum(), total_variance=values.sum()) == 3
    assert _choose_nconf(values, 3.0 / values.sum(), total_variance=values.sum()) == 1


def test_large_finite_eigenvalue_has_finite_lifting_and_coordinates():
    pc = np.array([[1e154, -1e154]])
    with np.errstate(over="raise", invalid="raise"):
        result = snapshot_decompose(pc, np.ones(1))
    assert result["info"]["numerical_rank"] == 1
    assert np.isfinite(result["info"]["total_variance"])
    for key in ("eigenvalues", "modes", "coordinates"):
        assert np.all(np.isfinite(result[key]))
    np.testing.assert_allclose(result["eigenvalues"], [1e308], rtol=1e-14)
    np.testing.assert_allclose(result["modes"] @ result["coordinates"].T, pc, rtol=1e-14)


@pytest.mark.parametrize("requested_rtol", [0.0, 1e-300])
def test_numerical_floor_prevents_lifting_roundoff_native_modes(requested_rtol):
    observed = np.array([0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.4, 12.8])
    observed -= observed.mean()
    native = np.array([1.0, -1.0, 2.0, -2.0, 3.0, -3.0, 4.0, -4.0])
    native -= observed * (native @ observed) / (observed @ observed)
    pc = np.vstack([observed, 0.3 * observed, native])
    result = snapshot_decompose(
        pc, np.array([1.0, 2.0, 0.0]),
        {"eig_rtol": requested_rtol, "eig_atol": 0.0},
    )
    info = result["info"]
    assert info["eig_rtol_requested"] == requested_rtol
    assert info["eig_rtol"] >= pc.shape[1] * np.finfo(float).eps
    assert info["numerical_rank"] == 1
    assert result["modes"].shape == (3, 1)
    reconstructed = result["modes"] @ result["coordinates"].T
    np.testing.assert_allclose(reconstructed[:2], pc[:2], rtol=1e-13, atol=1e-13)
    np.testing.assert_allclose(reconstructed[-1], 0.0, atol=1e-13)
    assert np.linalg.norm(native) > 1.0


@pytest.mark.parametrize("weights", [[1.0, 0.0], [0.0, 0.0]])
def test_zero_weighted_variance_has_no_fabricated_mode(weights):
    with pytest.raises(ValueError):
        snapshot_decompose(np.zeros((2, 4)), np.asarray(weights))


@pytest.mark.parametrize("weights", [[1.0, -1.0], [1.0, np.inf], [1.0, np.nan], [1.0]])
def test_invalid_metrics_are_rejected(weights):
    pc = np.array([[-1.0, 0.0, 1.0], [0.0, 1.0, -1.0]])
    with pytest.raises(ValueError):
        snapshot_decompose(pc, np.asarray(weights))


@pytest.mark.parametrize("options", [
    {"eig_atol": -1.0}, {"eig_rtol": np.nan}, {"block_rows": 0},
    {"block_rows": 1.5}, {"cluster_rtol": -1.0},
])
def test_invalid_snapshot_options_are_rejected(options):
    pc = np.array([[-1.0, 0.0, 1.0], [0.0, 1.0, -1.0]])
    with pytest.raises(ValueError):
        snapshot_decompose(pc, np.ones(2), options)


@pytest.mark.parametrize("mode", ["pme", "pi", "pd"])
def test_shared_case_matches_direct_reference_and_weight_builders(mode):
    from pme_toolkit.model import _compose_p, _prepare_vars, _slice_blocks

    db, cfg, urange = _case(mode)
    model = fit_model(db, cfg, urange_full=urange)
    blocks = _slice_blocks(db, model.layout)
    uact, uinfo = _prepare_vars(blocks["Ubase"], cfg, urange)
    p = _compose_p(mode, blocks["D"], uact, blocks["F"], blocks["C"])
    delta = p - p[:, [0]]
    dense, stats_dense = build_weights(delta, model.layout, cfg, uinfo, blocks)
    vector, stats_vector = build_weights_diag(delta, model.layout, cfg, uinfo, blocks)
    np.testing.assert_allclose(vector, np.diag(dense), rtol=0, atol=0)
    assert stats_dense == stats_vector

    values, modes, scores = _direct_reference(model.pc, model.w)
    n = model.nconf
    np.testing.assert_allclose(model.eigvals_full, values, rtol=1e-11, atol=1e-13)
    np.testing.assert_allclose(
        model.z_reduced @ model.alpha_train.T, modes[:, :n] @ scores[:, :n].T,
        atol=2e-11,
    )
    np.testing.assert_allclose(model.transform(db), model.alpha_train, atol=2e-11)
    total = np.sum(model.w * np.var(model.pc, axis=1))
    info = model.stats_w["snapshot"]
    assert info["total_variance"] == pytest.approx(total)
    assert info["achieved_ci"] == pytest.approx(model.eigvals_reduced.sum() / total)
    assert info["ci_met"]
    if mode in ("pi", "pd"):
        # The constant scalar counts as an information source, but adds no variance.
        assert total == pytest.approx(model.stats_w["ninfo"]["total"] - 1)


def test_unreachable_ci_is_reported_after_rank_cutoff():
    db, cfg, urange = _case("pi")
    cfg["snapshot"]["eig_rtol"] = 0.5
    cfg["CI"] = 0.999
    with pytest.warns(RuntimeWarning):
        model = fit_model(db, cfg, urange_full=urange)
    info = model.stats_w["snapshot"]
    assert not info["ci_met"]
    assert info["achieved_ci"] < cfg["CI"]
    assert model.nconf == info["numerical_rank"]


def test_legacy_dense_weight_archive_still_loads(tmp_path):
    db, cfg, urange = _case("pi")
    model = fit_model(db, cfg, urange_full=urange)
    current = tmp_path / "current.npz"
    model.save(current)
    with np.load(current, allow_pickle=False) as archive:
        legacy_data = {name: archive[name] for name in archive.files}
    legacy_data["w"] = np.diag(model.w)
    legacy_stats = json.loads(str(legacy_data["stats_w_json"]))
    legacy_stats.pop("snapshot")
    legacy_data["stats_w_json"] = json.dumps(legacy_stats)
    legacy_path = tmp_path / "legacy.npz"
    np.savez_compressed(legacy_path, **legacy_data)

    for path in (current, legacy_path):
        loaded = PmeModel.load(path)
        assert loaded.w.ndim == 1
        np.testing.assert_allclose(loaded.transform(db), model.alpha_train, atol=2e-11)
        np.testing.assert_allclose(
            loaded.inverse_full(model.alpha_train), model.inverse_full(model.alpha_train),
            atol=2e-11,
        )


def test_reports_use_weighted_variance_with_a_constant_source():
    from pme_toolkit.plotting import _reconstruction_curves as plotting_curves
    from pme_toolkit.report import _reconstruction_curves as report_curves, build_report

    cfg = {
        "mode": "pi", "CI": 0.95, "baseline_col": 1,
        "geom": {"Jdir": 2, "patches": [{"name": "surface", "K": 1}]},
        "vars": {"Mbase": 1, "idx_active": []},
        "phys": {"fields": [], "scalars": [{"name": "constant", "nCond": 1}]},
    }
    db = np.array([[-1, 0, 1, 0], [0, -1, 0, 1], [0, 1, 0, -1], [7, 7, 7, 7]], dtype=float)
    model = fit_model(db, cfg, urange_full=np.array([[-1.0, 1.0]]))
    assert model.nconf == 2 > model.uinfo["Mact"]
    assert model.stats_w["ninfo"]["total"] == 2
    assert model.stats_w["snapshot"]["total_variance"] == pytest.approx(1.0)

    rec = report_curves(model)
    plotted = plotting_curves(model)
    np.testing.assert_allclose(rec["retained_variance"], [0.5, 1.0], atol=2e-13)
    np.testing.assert_allclose(rec["ev_global"], rec["retained_variance"], atol=2e-13)
    np.testing.assert_allclose(plotted["retained_variance"], rec["retained_variance"], atol=2e-13)
    np.testing.assert_allclose(plotted["ev_global"], rec["ev_global"], atol=2e-13)
    report = build_report(model)
    assert report["krep"] == 2
    assert report["global_check"]["eig_ratio"] == pytest.approx(1.0)
    assert report["global_check"]["diff"] == pytest.approx(0.0, abs=2e-13)
