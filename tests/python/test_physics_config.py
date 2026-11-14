import json
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest

from pme_toolkit.config_loader import load_case_json
from pme_toolkit.model import fit_from_case, fit_pme
from pme_toolkit.run_case import run_case


MISSING = object()
INVALID_PHYSICS = [MISSING, None, {}, {"fields": [], "scalars": []}, []]
INVALID_IDS = ["missing", "null", "empty-object", "empty-sources", "wrong-container"]
ERROR_MATCH = r"requires at least one physical field or scalar in cfg\.phys"


def _case(mode: str = "pme") -> dict:
    return {
        "mode": mode,
        "baseline_col": 0,
        "geom": {"Jdir": 2, "patches": [{"name": "P1", "K": 1}]},
        "vars": {"Mbase": 1, "idx_active": []},
    }


def _database() -> np.ndarray:
    return np.array([
        [0.0, 0.2, 0.6, 1.0],
        [1.0, 0.8, 0.5, 0.1],
        [0.0, 1.0 / 3.0, 2.0 / 3.0, 1.0],
    ])


@pytest.mark.parametrize("mode", ["pi", "pd"])
@pytest.mark.parametrize("phys", INVALID_PHYSICS, ids=INVALID_IDS)
def test_json_rejects_missing_physics(tmp_path: Path, mode: str, phys) -> None:
    cfg = _case(mode)
    if phys is not MISSING:
        cfg["phys"] = deepcopy(phys)
    case_file = tmp_path / "case.json"
    case_file.write_text(json.dumps(cfg), encoding="utf-8")

    with pytest.raises(ValueError, match=ERROR_MATCH):
        load_case_json(case_file)


@pytest.mark.parametrize("mode", ["pi", "pd", "PI", "PD"])
@pytest.mark.parametrize("phys", INVALID_PHYSICS, ids=INVALID_IDS)
def test_direct_fit_rejects_missing_physics(mode: str, phys) -> None:
    cfg = _case(mode)
    if phys is not MISSING:
        cfg["phys"] = deepcopy(phys)

    with pytest.raises(ValueError, match=ERROR_MATCH):
        fit_pme(_database(), cfg)


@pytest.mark.parametrize("mode", ["pi", "pd"])
@pytest.mark.parametrize("runner", [run_case, fit_from_case])
def test_case_rejects_missing_physics_before_data_io(
    tmp_path: Path, mode: str, runner,
) -> None:
    cfg = _case(mode)
    cfg["io"] = {"dbfile": "missing.mat", "outdir": "results"}
    cfg["vars"]["Urange_file"] = "missing-range.mat"
    case_file = tmp_path / "case.json"
    case_file.write_text(json.dumps(cfg), encoding="utf-8")

    with pytest.raises(ValueError, match=ERROR_MATCH):
        runner(case_file)
    assert not (tmp_path / "results").exists()


@pytest.mark.parametrize("mode", ["pi", "pd", "PI", "PD"])
@pytest.mark.parametrize("source", ["fields", "scalars"])
def test_valid_physics_source_is_used(tmp_path: Path, mode: str, source: str) -> None:
    cfg = _case(mode)
    item = {"name": "response", "nCond": 1}
    if source == "fields":
        item["disc"] = {"K": 1}
    cfg["phys"] = {source: [item]}
    case_file = tmp_path / "case.json"
    case_file.write_text(json.dumps(cfg), encoding="utf-8")
    loaded, _ = load_case_json(case_file)
    db = np.vstack([_database(), [1.0, 2.0, 4.0, 3.0]])

    model = fit_pme(db, loaded)

    assert model.mode == mode.lower()
    assert model.layout["F"]["nRows"] + model.layout["C"]["nRows"] == 1
    assert model.stats_w["ninfo"]["F"] + model.stats_w["ninfo"]["C"] == 1
    assert np.all(np.isfinite(model.eigvals_reduced))


@pytest.mark.parametrize("mode", [None, "pme", "PME"])
def test_geometry_only_pme_still_works(tmp_path: Path, mode: str | None) -> None:
    cfg = _case()
    if mode is None:
        del cfg["mode"]
    else:
        cfg["mode"] = mode
    case_file = tmp_path / "case.json"
    case_file.write_text(json.dumps(cfg), encoding="utf-8")
    loaded, _ = load_case_json(case_file)

    model = fit_pme(_database(), loaded)

    assert model.mode == "pme"
    assert model.layout["F"]["nRows"] == model.layout["C"]["nRows"] == 0
    assert np.all(np.isfinite(model.eigvals_reduced))
