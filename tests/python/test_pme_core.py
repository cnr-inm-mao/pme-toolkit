from pathlib import Path

import numpy as np

from pme_toolkit.io import load_mat_database, load_mat_range
from pme_toolkit.model import fit_pme
from pme_toolkit.config_loader import load_config


def test_fit_pme_on_tiny_glider_database() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    cfg_path = repo_root / "benchmarks" / "standard" / "pme" / "glider" / "case.json"
    cfg = load_config(cfg_path)

    db = load_mat_database(repo_root / "tests" / "data" / "glider_tiny.mat")
    urange = load_mat_range(repo_root / "tests" / "data" / "glider_range.mat")

    model = fit_pme(db, cfg, urange_full=urange)

    assert model.mode == "pme"
    assert model.nconf >= 1
    assert model.z_reduced.shape[1] == model.nconf
    assert model.alpha_train.shape[1] == model.nconf
    assert np.all(model.eigvals_reduced >= 0.0)


def test_transform_training_db_shape_consistency() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    cfg_path = repo_root / "benchmarks" / "standard" / "pme" / "glider" / "case.json"
    cfg = load_config(cfg_path)

    db = load_mat_database(repo_root / "tests" / "data" / "glider_tiny.mat")
    urange = load_mat_range(repo_root / "tests" / "data" / "glider_range.mat")

    model = fit_pme(db, cfg, urange_full=urange)
    alpha = model.transform(db)

    assert alpha.shape[0] == db.shape[1]
    assert alpha.shape[1] == model.nconf


def test_inverse_active_returns_expected_shape() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    cfg_path = repo_root / "benchmarks" / "standard" / "pme" / "glider" / "case.json"
    cfg = load_config(cfg_path)

    db = load_mat_database(repo_root / "tests" / "data" / "glider_tiny.mat")
    urange = load_mat_range(repo_root / "tests" / "data" / "glider_range.mat")

    model = fit_pme(db, cfg, urange_full=urange)

    alpha0 = model.alpha_train[:3, :]
    uact = model.inverse_active(alpha0)

    assert uact.shape == (3, model.uinfo["Mact"])
    assert np.all(np.isfinite(uact))
