from pathlib import Path

import numpy as np
from scipy.io import loadmat

from pme_toolkit.run_case import run_case


def _as_real_array(x, *, tol: float = 1e-12) -> np.ndarray:
    x = np.asarray(x)

    if np.iscomplexobj(x):
        imag_max = np.max(np.abs(np.imag(x)))
        assert imag_max < tol, (
            f"Non-negligible imaginary part found in MATLAB reference: "
            f"max(|imag|)={imag_max:.3e}"
        )
        x = np.real(x)

    return np.asarray(x, dtype=float)


def _align_mode_signs(
    zr_py: np.ndarray,
    zr_ref: np.ndarray,
    *,
    nconf: int,
) -> np.ndarray:
    zr_py = np.array(zr_py, dtype=float, copy=True)

    for k in range(nconf):
        dot = float(np.dot(zr_py[:, k], zr_ref[:, k]))
        sign = 1.0 if dot >= 0.0 else -1.0
        zr_py[:, k] *= sign

    return zr_py


def test_regression_against_matlab_reference() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    case_json = repo_root / "tests" / "cases" / "test_glider.json"
    ref_file = repo_root / "tests" / "reference" / "matlab_glider_reference.mat"

    assert case_json.is_file(), f"Missing test case file: {case_json}"
    assert ref_file.is_file(), f"Missing MATLAB reference file: {ref_file}"

    out = run_case(
        case_json,
        save_plots=False,
        n_modes_plot=2,
        print_text_report=False,
    )

    model_py = out["model"]
    rep_py = out["report"]

    mat = loadmat(ref_file)

    nconf_ref = int(np.asarray(mat["nconf"]).squeeze())
    lr_ref = _as_real_array(mat["Lr"]).reshape(-1)
    zr_ref = _as_real_array(mat["Zr"])

    nconf_py = int(rep_py["nconf"])
    eigvals_py = _as_real_array(model_py.eigvals_reduced).reshape(-1)
    zr_py = _as_real_array(model_py.z_reduced)

    assert nconf_py == nconf_ref, (
        f"Regression failed on nconf: expected {nconf_ref}, got {nconf_py}"
    )

    assert zr_py.shape == zr_ref.shape, (
        f"Reduced mode matrix shape mismatch: "
        f"Python {zr_py.shape} vs MATLAB {zr_ref.shape}"
    )

    np.testing.assert_allclose(
        eigvals_py[:nconf_ref],
        lr_ref[:nconf_ref],
        rtol=1e-8,
        atol=1e-10,
        err_msg="Reduced eigenvalues do not match MATLAB reference",
    )

    zr_py_aligned = _align_mode_signs(
        zr_py,
        zr_ref,
        nconf=nconf_ref,
    )

    np.testing.assert_allclose(
        zr_py_aligned[:, :nconf_ref],
        zr_ref[:, :nconf_ref],
        rtol=1e-7,
        atol=1e-9,
        err_msg="Reduced modes do not match MATLAB reference after sign alignment",
    )
