"""Compare the published airfoil benchmark with the pre-snapshot implementation.

The default run uses the complete Zenodo database and the existing standard
case filters. No columns are subsampled. The original implementation is loaded
unchanged from a separate checkout, identified by ``LEGACY_COMMIT``.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
from scipy.io import loadmat
from scipy.linalg import eigh

from pme_toolkit.config_loader import load_case_json
from pme_toolkit.datasets import ensure_case_inputs
from pme_toolkit.io import load_mat_database
from pme_toolkit.model import fit_model


LEGACY_COMMIT = "68309805e9aff5a9b877c33982c7181d8faa550b"
DATABASE_SHA256 = "a662f691c90158503ad627d1e4c36edafe566ec2fedb2ef3cadaacbb509cc177"
MODES = ("pme", "pi", "pd")


def _legacy_module(root: Path):
    package_dir = root / "python" / "src" / "pme_toolkit"
    spec = importlib.util.spec_from_file_location(
        "pme_legacy", package_dir / "__init__.py",
        submodule_search_locations=[str(package_dir)],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load the legacy package at {package_dir}")
    package = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = package
    spec.loader.exec_module(package)
    return importlib.import_module("pme_legacy.model")


def _source_identity(repo: Path, package_root: Path, *, ref: str | None = None) -> dict:
    """Hash solver inputs and verify that the legacy source is unchanged."""
    names = ("model.py", "weights.py", "filters.py", "layout.py", "config_loader.py")
    if ref is None:
        names += ("snapshot.py",)
    hashes = {}
    for name in names:
        content = (package_root / name).read_bytes()
        relative = f"python/src/pme_toolkit/{name}"
        if ref is not None:
            expected = subprocess.check_output(["git", "show", f"{ref}:{relative}"], cwd=repo)
            if content != expected:
                raise AssertionError(f"Legacy source differs from {ref}: {relative}")
        hashes[relative] = hashlib.sha256(content).hexdigest()
    return hashes


def prepare_dataset(repo: Path) -> tuple[np.ndarray, dict[str, dict], str]:
    configs = {}
    for mode in MODES:
        folder = "pme" if mode == "pme" else f"{mode}_pme"
        case = repo / "benchmarks" / "standard" / folder / "airfoil" / "case.json"
        cfg, _ = load_case_json(case)
        configs[mode] = cfg
    ensure_case_inputs(configs["pi"], repo / "benchmarks" / "standard" / "pi_pme" / "airfoil")
    database_path = Path(configs["pi"]["io"]["dbfile"])
    digest = hashlib.sha256(database_path.read_bytes()).hexdigest()
    if digest != DATABASE_SHA256:
        raise AssertionError(f"Unexpected airfoil database SHA256: {digest}")
    db = load_mat_database(database_path)
    if db.shape != (410, 16385):
        raise AssertionError(f"Unexpected airfoil database shape: {db.shape}")
    return db, configs, digest


def _native_rows(model) -> np.ndarray:
    start = 0 if model.mode == "pd" else int(model.layout["D"]["nRows"])
    return np.arange(start, start + int(model.uinfo["Mact"]))


def _reference(pc: np.ndarray, w: np.ndarray, threshold: float) -> dict:
    """Independent symmetric observation-space eigensolve (no Gram matrix)."""
    positive = w > 0
    b = np.sqrt(w[positive, None]) * pc[positive]
    covariance = b @ b.T / pc.shape[1]
    values, vectors = eigh((covariance + covariance.T) / 2)
    keep = values > threshold
    values = values[keep][::-1]
    vectors = vectors[:, keep][:, ::-1]
    a = (b.T @ vectors) / (np.sqrt(pc.shape[1]) * np.sqrt(values)[None, :])
    modes = pc @ (a / (np.sqrt(pc.shape[1]) * np.sqrt(values)[None, :]))
    coordinates = a * (np.sqrt(pc.shape[1]) * np.sqrt(values)[None, :])
    return {"values": values, "modes": modes, "coordinates": coordinates,
            "trace": float(np.trace(covariance))}


def compare_modes(values: np.ndarray, modes: np.ndarray, coordinates: np.ndarray,
                  reference_values: np.ndarray, reference_modes: np.ndarray,
                  reference_coordinates: np.ndarray, weights: np.ndarray,
                  nconf: int, native_rows: np.ndarray) -> dict:
    """Use signs for simple eigenvalues and projectors for repeated clusters."""
    values = np.asarray(values, dtype=float).reshape(-1)
    reference_values = np.asarray(reference_values, dtype=float).reshape(-1)
    modes = np.real_if_close(modes, tol=1000)
    reference_modes = np.real_if_close(reference_modes, tol=1000)
    if np.iscomplexobj(modes) or np.iscomplexobj(reference_modes):
        raise AssertionError("Non-negligible complex eigenvectors in regression")
    n = int(nconf)
    sqrt_w = np.sqrt(weights)[:, None]
    q = sqrt_w * modes[:, :n]
    qref = sqrt_w * reference_modes[:, :n]
    signs = np.where(np.sum(q * qref, axis=0) < 0, -1.0, 1.0)
    gaps = np.abs(np.diff(reference_values[:n]))
    cluster_boundary = gaps <= 1e-10 * np.maximum(reference_values[:n-1], reference_values[1:n])
    isolated = np.ones(n, dtype=bool)
    isolated[:-1] &= ~cluster_boundary
    isolated[1:] &= ~cluster_boundary
    mode_errors = np.linalg.norm(q * signs - qref, axis=0)
    native = modes[native_rows, :n] * signs
    native_ref = reference_modes[native_rows, :n]
    native_errors = np.linalg.norm(native - native_ref, axis=0) / np.maximum(
        np.linalg.norm(native_ref, axis=0), np.finfo(float).eps)
    u = modes[native_rows, :n] @ coordinates[:, :n].T
    uref = reference_modes[native_rows, :n] @ reference_coordinates[:, :n].T
    rank = min(values.size, reference_values.size)
    result = {
        "retained_eigenvalues_max_relative_error": float(np.max(
            np.abs(values[:n] - reference_values[:n]) / reference_values[:n])),
        "resolved_eigenvalues_max_error_over_lambda1": float(np.max(
            np.abs(values[:rank] - reference_values[:rank])) / reference_values[0]),
        "weighted_retained_projector_fro_error": float(np.linalg.norm(q @ q.T - qref @ qref.T)),
        "isolated_retained_mode_count": int(np.count_nonzero(isolated)),
        "weighted_isolated_modes_max_sign_aligned_error": float(np.max(mode_errors[isolated], initial=0)),
        "native_isolated_modes_max_sign_aligned_relative_error": float(np.max(native_errors[isolated], initial=0)),
        "native_reconstruction_relative_error": float(np.linalg.norm(u-uref) / np.linalg.norm(uref)),
    }
    assert result["retained_eigenvalues_max_relative_error"] < 5e-9, result
    assert result["resolved_eigenvalues_max_error_over_lambda1"] < 5e-9, result
    assert result["weighted_retained_projector_fro_error"] < 5e-7, result
    assert result["weighted_isolated_modes_max_sign_aligned_error"] < 5e-7, result
    assert result["native_isolated_modes_max_sign_aligned_relative_error"] < 5e-7, result
    assert result["native_reconstruction_relative_error"] < 5e-7, result
    return result


def _model_compare(candidate, legacy) -> dict:
    weights = np.asarray(candidate.w).reshape(-1)
    legacy_weights = np.diag(legacy.w) if legacy.w.ndim == 2 else legacy.w
    np.testing.assert_allclose(weights, legacy_weights, rtol=2e-12, atol=1e-12)
    np.testing.assert_array_equal(candidate.filter_mask, legacy.filter_mask)
    assert candidate.nconf == legacy.nconf, (candidate.nconf, legacy.nconf)
    return compare_modes(
        candidate.eigvals_full, candidate.z_full, candidate.ak_full,
        legacy.eigvals_full, legacy.z_full, legacy.ak_full, weights,
        candidate.nconf, _native_rows(candidate),
    )


def run(repo: Path, legacy_root: Path, output: Path, *, solvers: list[str],
        matlab_result: Path | None = None, matlab_legacy_result: Path | None = None) -> dict:
    db, configs, digest = prepare_dataset(repo)
    legacy_fit = _legacy_module(legacy_root).fit_model
    result = {"dataset": {
        "name": "RAE2822 airfoil", "doi": "10.5281/zenodo.18958555",
        "url": "https://zenodo.org/records/18958555",
        "database_sha256": digest, "original_shape": list(db.shape),
        "sampling": "All published columns; existing standard case filters only",
    }, "legacy_commit": LEGACY_COMMIT,
        "current_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
        "current_worktree_modified": bool(subprocess.check_output(
            ["git", "status", "--porcelain", "--", "python/src/pme_toolkit"], cwd=repo, text=True).strip()),
        "current_source_sha256": _source_identity(repo, repo / "python" / "src" / "pme_toolkit"),
        "legacy_source_sha256": _source_identity(repo, legacy_root / "python" / "src" / "pme_toolkit", ref=LEGACY_COMMIT),
        "cases": {}}
    matlab = loadmat(matlab_result, simplify_cells=True)["results"] if matlab_result else None
    matlab_legacy = (loadmat(matlab_legacy_result, simplify_cells=True)["results"]
                     if matlab_legacy_result else None)
    for mode in MODES:
        cfg = deepcopy(configs[mode])
        print(f"{mode.upper()}: fitting unchanged legacy implementation", flush=True)
        start = time.perf_counter()
        legacy = legacy_fit(db, deepcopy(cfg))
        case = {"kept_samples": int(legacy.pc.shape[1]), "legacy_nconf": int(legacy.nconf),
                "legacy_seconds": time.perf_counter()-start, "solvers": {}}
        legacy_trace = float(np.sum(legacy.eigvals_full))
        legacy_ci = float(np.sum(legacy.eigvals_reduced) / legacy_trace)
        for solver in solvers:
            cfg["solver"] = solver
            print(f"{mode.upper()}: fitting {solver} on all {legacy.pc.shape[1]} retained samples", flush=True)
            start = time.perf_counter()
            current = fit_model(db, deepcopy(cfg))
            elapsed = time.perf_counter()-start
            info = current.stats_w["snapshot"]
            comparison = _model_compare(current, legacy)
            reference = _reference(current.pc, current.w, info["eigenvalue_threshold"])
            direct_comparison = compare_modes(
                current.eigvals_full, current.z_full, current.ak_full,
                reference["values"], reference["modes"], reference["coordinates"],
                current.w, current.nconf, _native_rows(current),
            )
            ci_error = abs(info["achieved_ci"] - legacy_ci)
            assert ci_error < 5e-10, ci_error
            np.testing.assert_allclose(info["total_variance"], reference["trace"], rtol=2e-12)
            record = {
                "requested_solver": solver, "effective_solver": info.get("solver", "snapshot"),
                "seconds": elapsed, "nconf": current.nconf,
                "numerical_rank": info["numerical_rank"],
                "total_variance": info["total_variance"],
                "achieved_ci": info["achieved_ci"], "legacy_achieved_ci": legacy_ci,
                "achieved_ci_absolute_error": ci_error,
                "retained_eigenvalues": current.eigvals_reduced.tolist(),
                "versus_legacy": comparison,
                "versus_symmetric_direct_reference": direct_comparison,
            }
            if matlab is not None:
                m = matlab[mode][solver]
                np.testing.assert_array_equal(np.asarray(m["filter_mask"]).astype(bool), current.filter_mask)
                assert int(m["nconf"]) == current.nconf
                np.testing.assert_allclose(np.asarray(m["weights"]).ravel(), current.w, rtol=2e-11, atol=2e-11)
                record["versus_matlab"] = compare_modes(
                    current.eigvals_full, current.z_full, current.ak_full,
                    np.asarray(m["values"]).ravel(), np.asarray(m["modes"]),
                    np.asarray(m["coordinates"]), current.w, current.nconf, _native_rows(current),
                )
                np.testing.assert_allclose(m["achieved_ci"], info["achieved_ci"], rtol=2e-11)
            if matlab_legacy is not None:
                m = matlab_legacy[mode]["legacy"]
                np.testing.assert_array_equal(np.asarray(m["filter_mask"]).astype(bool), current.filter_mask)
                assert int(m["nconf"]) == current.nconf
                np.testing.assert_allclose(np.asarray(m["weights"]).ravel(), current.w, rtol=2e-11, atol=2e-11)
                record["versus_legacy_matlab"] = compare_modes(
                    current.eigvals_full, current.z_full, current.ak_full,
                    np.asarray(m["values"]).ravel(), np.asarray(m["modes"]),
                    np.asarray(m["coordinates"]), current.w, current.nconf, _native_rows(current),
                )
                np.testing.assert_allclose(m["achieved_ci"], info["achieved_ci"], rtol=2e-11)
            case["solvers"][solver] = record
            print(f"{mode.upper()} {solver}: N={current.nconf}, variance={info['achieved_ci']:.12f}, "
                  f"eigenvalue relative error={comparison['retained_eigenvalues_max_relative_error']:.3e}, "
                  f"mode error={comparison['weighted_isolated_modes_max_sign_aligned_error']:.3e}, "
                  f"elapsed={elapsed:.1f}s", flush=True)
            for label in ("versus_matlab", "versus_legacy_matlab"):
                if label in record:
                    check = record[label]
                    print(f"{mode.upper()} {solver} {label}: "
                          f"eigenvalue relative error={check['retained_eigenvalues_max_relative_error']:.3e}, "
                          f"weighted mode error={check['weighted_isolated_modes_max_sign_aligned_error']:.3e}, "
                          f"native reconstruction error={check['native_reconstruction_relative_error']:.3e}",
                          flush=True)
            del current
        result["cases"][mode] = case
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Zenodo regression passed; report: {output}", flush=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--solvers", nargs="+", default=["auto", "direct", "snapshot"])
    parser.add_argument("--matlab-result", type=Path)
    parser.add_argument("--matlab-legacy-result", type=Path)
    args = parser.parse_args()
    run(Path(__file__).resolve().parents[2], args.legacy_root.resolve(), args.output.resolve(),
        solvers=args.solvers, matlab_result=args.matlab_result,
        matlab_legacy_result=args.matlab_legacy_result)


if __name__ == "__main__":
    main()
