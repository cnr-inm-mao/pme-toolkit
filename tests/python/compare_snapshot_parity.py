"""Compare current MATLAB and Python fits on the shared snapshot database.

Run after tests/matlab/export_snapshot_parity.m:
    python tests/python/compare_snapshot_parity.py /tmp/snapshot_parity.json
"""

import argparse
import json
from copy import deepcopy
from pathlib import Path

import numpy as np

from pme_toolkit.model import fit_model


def compare(reference_path: Path) -> None:
    fixture_path = Path(__file__).resolve().parents[1] / "data" / "snapshot_parity.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    references = json.loads(reference_path.read_text(encoding="utf-8"))
    db = np.asarray(fixture["db"], dtype=float)
    urange = np.asarray(fixture["urange"], dtype=float)

    for mode in ("pme", "pi", "pd"):
        cfg = deepcopy(fixture["cfg"])
        cfg["mode"] = mode
        model = fit_model(db, cfg, urange_full=urange)
        reference = references[mode]
        assert model.nconf == int(reference["nconf"]), f"{mode}: retained dimension differs"
        np.testing.assert_allclose(
            model.eigvals_reduced, np.asarray(reference["eigenvalues"]).reshape(-1),
            rtol=1e-10, atol=1e-12, err_msg=f"{mode}: eigenvalues",
        )
        np.testing.assert_allclose(
            model.w, np.asarray(reference["weights"]).reshape(-1),
            rtol=2e-13, atol=1e-13, err_msg=f"{mode}: weights",
        )
        start = 0 if mode == "pd" else model.layout["D"]["nRows"]
        stop = start + model.uinfo["Mact"]
        native = model.z_reduced[start:stop] @ model.alpha_train.T
        np.testing.assert_allclose(
            native, reference["native_reconstruction"], rtol=1e-9, atol=1e-11,
            err_msg=f"{mode}: centered native reconstruction",
        )
        a = model.alpha_train / np.sqrt(db.shape[1] * model.eigvals_reduced)
        np.testing.assert_allclose(
            a @ a.T, reference["sample_projector"], rtol=1e-9, atol=1e-11,
            err_msg=f"{mode}: retained sample subspace",
        )
        for key in ("total_variance", "achieved_ci"):
            np.testing.assert_allclose(
                model.stats_w["snapshot"][key], reference[key], rtol=1e-11, atol=1e-13,
                err_msg=f"{mode}: {key}",
            )
        print(f"{mode.upper()}: MATLAB/Python snapshot parity passed (N={model.nconf})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path, help="JSON written by export_snapshot_parity.m")
    args = parser.parse_args()
    compare(args.reference)
