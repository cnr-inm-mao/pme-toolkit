"""Exercise configured database orientation and optional model persistence."""

import json
from pathlib import Path

import numpy as np
import pytest
from scipy.io import savemat

from pme_toolkit.io import load_mat_database, orient_database
from pme_toolkit.model import PmeModel
from pme_toolkit.run_back import run_back
from pme_toolkit.run_case import run_case


def _case(tmp_path, *, transpose_if="never", transposed=False, save_model=True):
    t = np.linspace(0.0, 1.0, 8)
    database = np.vstack([t, t**2, t])
    savemat(tmp_path / "database.mat", {"database": database.T if transposed else database})
    cfg = {
        "mode": "pme", "CI": 0.95, "baseline_col": 0,
        "geom": {"Jdir": 2, "patches": [{"K": 1}]},
        "vars": {"Mbase": 1, "idx_active": [], "use_db_range_if_missing": True},
        "filters": {"remove_nan": True},
        "io": {"dbfile": "database.mat", "outdir": "results", "transpose_if": transpose_if},
    }
    if save_model is not None:
        cfg["io"]["save_model"] = save_model
    casefile = tmp_path / "case.json"
    casefile.write_text(json.dumps(cfg), encoding="utf-8")
    return casefile, database


@pytest.mark.parametrize("policy,transposed", [
    ("auto", False), ("auto", True), ("always", True), ("never", False),
])
def test_run_case_applies_orientation_once(tmp_path: Path, policy, transposed):
    casefile, expected = _case(tmp_path, transpose_if=policy, transposed=transposed,
                               save_model=False)
    raw = load_mat_database(tmp_path / "database.mat")
    np.testing.assert_array_equal(raw, expected.T if transposed else expected)
    out = run_case(casefile, save_plots=False, print_text_report=False)
    np.testing.assert_array_equal(out["DB"], expected)
    assert out["model"].alpha_train.shape[0] == expected.shape[1]
    np.testing.assert_allclose(
        out["model"].transform(expected), out["model"].alpha_train, atol=1e-12,
    )


def test_auto_requires_an_exact_layout_match_and_never_keeps_extra_rows():
    database = np.arange(24).reshape(4, 6)
    with pytest.raises(ValueError, match="layout.totalRows=3"):
        orient_database(database, 3)
    np.testing.assert_array_equal(orient_database(database, 3, "never"), database)
    square = np.arange(9).reshape(3, 3)
    np.testing.assert_array_equal(orient_database(square, 3, "auto"), square)
    np.testing.assert_array_equal(orient_database(square, 3, "always"), square.T)


@pytest.mark.parametrize("policy", ["invalid", "", None])
def test_invalid_orientation_is_rejected(policy):
    with pytest.raises(ValueError, match="io.transpose_if"):
        orient_database(np.zeros((3, 4)), 3, policy)


@pytest.mark.parametrize("save_model", [True, False, None])
def test_model_persistence_respects_configuration(tmp_path: Path, save_model):
    casefile, _ = _case(tmp_path, save_model=save_model)
    out = run_case(casefile, save_plots=False, print_text_report=False)
    model_path = Path(out["outdir"]) / "model.npz"
    assert Path(out["saved"]["report_mat"]).is_file()
    if save_model is False:
        assert not model_path.exists()
        assert "model_npz" not in out["saved"]
    else:
        assert out["saved"]["model_npz"] == str(model_path)
        restored = PmeModel.load(model_path)
        np.testing.assert_array_equal(restored.eigvals_reduced, out["model"].eigvals_reduced)


def test_disabled_persistence_keeps_existing_model_file(tmp_path: Path):
    casefile, _ = _case(tmp_path, save_model=False)
    model_path = tmp_path / "results" / "model.npz"
    model_path.parent.mkdir()
    original = b"Existing model file must not be overwritten or removed."
    model_path.write_bytes(original)
    out = run_case(casefile, save_plots=False, print_text_report=False)
    assert model_path.read_bytes() == original
    assert "model_npz" not in out["saved"]
    assert out["model"].nconf > 0


def test_fit_and_backmapping_share_default_output_directory(tmp_path: Path):
    casefile, database = _case(tmp_path)
    cfg = json.loads(casefile.read_text(encoding="utf-8"))
    cfg["io"].pop("outdir")
    casefile.write_text(json.dumps(cfg), encoding="utf-8")
    fitted = run_case(casefile, save_plots=False, print_text_report=False)
    expected_dir = tmp_path / "results"
    assert Path(fitted["outdir"]) == expected_dir
    assert not (tmp_path / "results_py").exists()

    backfile = tmp_path / "backmapping.json"
    backfile.write_text(json.dumps({
        "case_json": "case.json",
        "output": {"file": "results/recovered.txt", "what": "Ubase"},
    }), encoding="utf-8")
    recovered = run_back(backfile, x01=np.full(fitted["model"].nconf, 0.5))
    assert Path(recovered["outdir"]) == expected_dir
    assert Path(recovered["model_file"]) == expected_dir / "model.npz"
    assert Path(recovered["written_files"]["vector_file"]) == expected_dir / "recovered.txt"
    np.testing.assert_allclose(recovered["U"], [database[2].mean()], atol=1e-12)
