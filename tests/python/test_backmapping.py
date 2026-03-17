from pathlib import Path
import json

import numpy as np

from pme_toolkit.run_case import run_case
from pme_toolkit.run_back import run_back


def test_run_back_override_writes_case_results():
    repo_root = Path(__file__).resolve().parents[2]

    case_json = repo_root / "tests" / "cases" / "test_glider.json"
    cfg = repo_root / "tests" / "cases" / "test_glider_back.json"
    outdir = repo_root / "tests" / "cases" / "results"
    ufile = outdir / "u_base.txt"
    mfile = outdir / "u_base.txt.meta.json"
    model_file = outdir / "model.npz"

    # ensure model exists, as required by standalone backmapping
    run_case(
        case_json,
        save_plots=False,
        n_modes_plot=2,
        print_text_report=False,
    )

    assert model_file.exists()

    # cleanup previous backmapping outputs only
    if ufile.exists():
        ufile.unlink()
    if mfile.exists():
        mfile.unlink()

    x01 = np.full(5, 0.5, dtype=float)

    out = run_back(cfg, x01=x01)

    assert isinstance(out, dict)
    assert "U" in out

    u = np.asarray(out["U"], dtype=float).reshape(-1)
    assert u.ndim == 1
    assert u.size > 0

    assert ufile.exists()
    assert mfile.exists()

    u_saved = np.loadtxt(ufile, dtype=float)
    u_saved = np.asarray(u_saved, dtype=float).reshape(-1)
    assert u_saved.shape == u.shape
    assert np.all(np.isfinite(u_saved))

    with mfile.open("r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["schema"] == "pme.backmapping.v1"
    assert meta["what"] == "Ubase"
    assert int(meta["nconf_use"]) == 5
    assert int(meta["nconf_model"]) >= 5
    assert Path(meta["model_file"]).name == "model.npz"
