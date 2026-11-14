import json
from pathlib import Path

import numpy as np
import pytest

from pme_toolkit.config_loader import load_config
from pme_toolkit.model import fit_model


def test_load_benchmark_style_config() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    cfg_path = repo_root / "benchmarks" / "standard" / "pme" / "glider" / "case.json"

    cfg = load_config(cfg_path)

    assert isinstance(cfg, dict)
    assert cfg["mode"] == "pme"
    assert "geom" in cfg
    assert "vars" in cfg
    assert "io" in cfg
    assert Path(cfg["io"]["dbfile"]).is_absolute()


def _minimal_config():
    return {
        "mode": "pme",
        "geom": {"Jdir": 2, "patches": [{"name": "surface", "K": 1}]},
        "vars": {"Mbase": 1, "idx_active": []},
    }


def test_omitted_solver_confidence_and_range_match_explicit_defaults(tmp_path):
    cfg = _minimal_config()
    path = tmp_path / "case.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    db = np.array([[-1, 1, -1, 1], [-.2, -.2, .2, .2], [-2, -1, 1, 2]])
    model = fit_model(db, load_config(path))

    assert model.cfg["CI"] == .99
    assert model.cfg["solver"] == "auto"
    assert model.nconf == 2
    assert model.baseline_col == 0
    assert model.uinfo["Urange_source"] == "db"
    np.testing.assert_array_equal(model.uinfo["Urange"], [[-2, 2]])
    np.testing.assert_array_equal(model.p0[:, 0], [-1, -.2, 0])
    explicit = {**cfg, "solver": "auto", "CI": .99, "baseline_col": 0,
                "vars": {**cfg["vars"], "use_db_range_if_missing": True}}
    reference = fit_model(db, explicit)
    np.testing.assert_allclose(model.z_reduced, reference.z_reduced, atol=1e-14)
    np.testing.assert_allclose(model.alpha_train, reference.alpha_train, atol=1e-14)


def test_json_baseline_one_selects_second_sample_and_fixed_variables(tmp_path):
    cfg = _minimal_config()
    cfg["baseline_col"] = 1
    cfg["vars"] = {"Mbase": 2, "idx_active": [0]}
    path = tmp_path / "case.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    db = np.array([[-1, 1, -1, 1], [-.2, -.2, .2, .2],
                   [-2, -1, 1, 2], [10, 20, 30, 40]])
    model = fit_model(db, load_config(path))

    assert model.baseline_col == 1
    np.testing.assert_array_equal(model.p0[:, 0], [1, -.2, .25])
    np.testing.assert_array_equal(model.uinfo["Ubase_baseline_raw"], [-1, 20])
    reconstructed = model.inverse_full(model.alpha_train)
    np.testing.assert_array_equal(reconstructed[:, 1], np.full(4, 20))


def test_nonzero_baseline_is_mapped_after_nan_and_goal_filtering(tmp_path):
    cfg = _minimal_config()
    cfg.update(mode="pi", baseline_col=3)
    cfg["vars"] = {"Mbase": 2, "idx_active": [0]}
    cfg["phys"] = {"fields": [], "scalars": [{"name": "response", "nCond": 1}]}
    cfg["filters"] = {"remove_nan": True, "goal": {
        "enable": True, "baseline_col": 3,
        "metrics": [{"c_offset": 0, "rule": "leq_baseline", "factor": .9}],
    }}
    path = tmp_path / "case.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    db = np.array([[np.nan, 1, 2, 3, 4, 5], [0, 1, -1, .5, 2, -2],
                   [0, 10, 20, 30, 40, 50], [100, 110, 120, 130, 140, 150],
                   [0, 2, 7, 5, 8, 3]])
    model = fit_model(db, load_config(path))

    # The original fourth column survives even though it fails the goal's .9 factor.
    np.testing.assert_array_equal(model.filter_mask, [False, True, False, True, False, True])
    assert model.baseline_col == 1
    np.testing.assert_array_equal(model.p0[:, 0], [3, .5, .5, 5])
    np.testing.assert_array_equal(model.uinfo["Ubase_baseline_raw"], [30, 130])
    np.testing.assert_array_equal(model.inverse_full(model.alpha_train)[:, 1], [130, 130, 130])
    np.testing.assert_allclose(model.transform_valid(db), model.alpha_train, atol=1e-12)


@pytest.mark.parametrize("baseline", [-1, 4, 1.5, True])
def test_invalid_baseline_indices_are_rejected(baseline):
    cfg = _minimal_config()
    cfg["baseline_col"] = baseline
    db = np.array([[-1, 1, -1, 1], [-.2, -.2, .2, .2], [-2, -1, 1, 2]])
    with pytest.raises(ValueError, match="baseline_col"):
        fit_model(db, cfg)
