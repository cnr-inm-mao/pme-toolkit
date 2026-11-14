#!/usr/bin/env python3
"""Run controlled direct, snapshot and streamed PME verification experiments.

This driver uses the public toolkit solvers. The input fixture fixes the native
designs independently of random-number implementations in other languages.
Measured outputs belong to this protocol and do not reproduce unpublished
reference scripts merely by sharing their seed.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time

# The controlled experiments use one numerical-library thread. Set this before
# importing NumPy, including in the separate process used for memory measurement.
for _thread_variable in (
    "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS",
    "BLIS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS",
):
    os.environ[_thread_variable] = "1"

import numpy as np

from pme_toolkit.snapshot import direct_decompose, snapshot_decompose
from pme_toolkit.streaming import (
    backmap_streaming,
    fit_streaming,
    transform_streaming,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "data" / "snapshot_curve.json"
SEED = 20261020


def _relative(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.linalg.norm(left - right) / max(np.linalg.norm(right), np.finfo(float).tiny))


def _rss_bytes() -> int | None:
    """Return the process high-water resident set on Linux or macOS."""
    try:
        import resource
    except ImportError:
        return None
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == "darwin" else value * 1024)


def _environment() -> dict:
    hashes = {}
    sources = sorted((ROOT / "python" / "src" / "pme_toolkit").glob("*.py"))
    sources += [Path(__file__).resolve(), FIXTURE]
    for path in sources:
        hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    try:
        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
        dirty = bool(subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=ROOT, text=True
        ).strip())
    except (OSError, subprocess.CalledProcessError):
        revision, dirty = None, None
    try:
        installed_version = importlib.metadata.version("pme-toolkit")
    except importlib.metadata.PackageNotFoundError:
        installed_version = None
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "installed_distribution_version": installed_version,
        "git_head": revision,
        "working_tree_modified": dirty,
        "numerical_library_threads": 1,
        "source_sha256": hashes,
    }


def _fixture() -> tuple[dict, np.ndarray, np.ndarray]:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return payload, np.asarray(payload["native"], dtype=float), np.asarray(payload["query_native"], dtype=float)


def curve_rows(native: np.ndarray, rows: int, start: int, stop: int) -> np.ndarray:
    """Evaluate the manuscript curve at midpoint locations without full geometry."""
    t = (np.arange(start, stop, dtype=float) + 0.5) / rows
    j = np.arange(1, 9, dtype=float)
    linear = np.sin(np.pi * t[:, None] * j) * (0.04 / j**1.2)
    return (
        0.12 * np.sin(np.pi * t[:, None])
        + linear @ native
        + 0.025 * np.sin(9 * np.pi * t[:, None]) * (native[0] * native[1])[None, :]
    )


def _prescribed_data(spectrum: np.ndarray) -> tuple[np.ndarray, np.ndarray, int]:
    q, samples, native_rows = 160, 48, 6
    rng = np.random.default_rng(SEED)
    a = rng.normal(size=(samples, spectrum.size))
    a -= a.mean(axis=0, keepdims=True)
    a, _ = np.linalg.qr(a, mode="reduced")
    y, _ = np.linalg.qr(rng.normal(size=(q, spectrum.size)), mode="reduced")
    weights = np.linspace(0.2, 2.8, q)
    h = (y / np.sqrt(weights)[:, None] * np.sqrt(samples * spectrum)) @ a.T
    native = rng.normal(size=(native_rows, spectrum.size)) @ a.T
    return np.vstack([h, native]), np.r_[weights, np.zeros(native_rows)], q


def _comparison(pc: np.ndarray, weights: np.ndarray, direct: dict, snapshot: dict, n: int, q: int) -> dict:
    zd, zs = direct["modes"][:, :n], snapshot["modes"][:, :n]
    cd, cs = direct["coordinates"][:, :n], snapshot["coordinates"][:, :n]
    yd, ys = np.sqrt(weights[:q, None]) * zd[:q], np.sqrt(weights[:q, None]) * zs[:q]
    ld, ls = direct["eigenvalues"][:n], snapshot["eigenvalues"][:n]
    residual = pc @ (pc.T @ (weights[:, None] * zs)) / pc.shape[1] - zs * ls
    output = {
        "n": n,
        "max_relative_eigenvalue_difference": float(np.max(np.abs(ld - ls) / ld)),
        "weighted_projector_difference_fro": float(np.linalg.norm(yd @ yd.T - ys @ ys.T)),
        "relative_native_backmap_difference": _relative(zs[q:] @ cs.T, zd[q:] @ cd.T),
        "weighted_orthonormality_error_fro": float(np.linalg.norm(zs.T @ (weights[:, None] * zs) - np.eye(n))),
        "relative_augmented_eigen_residual": float(np.linalg.norm(residual) / np.linalg.norm(zs * ls)),
    }
    for metric in (
        "max_relative_eigenvalue_difference", "weighted_projector_difference_fro",
        "relative_native_backmap_difference", "weighted_orthonormality_error_fro",
        "relative_augmented_eigen_residual",
    ):
        if output[metric] > 1e-9:
            raise AssertionError(f"Controlled verification failed: N={n}, {metric}={output[metric]:.3e}")
    return output


def verify_prescribed() -> dict:
    spectrum = np.array([4.0, 1.0, 1.0, 0.1, 0.01, 0.001])
    pc, weights, q = _prescribed_data(spectrum)
    options = {"eig_rtol": 1e-12, "eig_atol": 0.0, "cluster_rtol": 1e-10, "block_rows": 31}
    direct = direct_decompose(pc, weights, options)
    snapshot = snapshot_decompose(pc, weights, options)
    np.testing.assert_allclose(direct["eigenvalues"], spectrum, rtol=1e-10, atol=1e-13)
    np.testing.assert_allclose(snapshot["eigenvalues"], spectrum, rtol=1e-10, atol=1e-13)
    return {
        "observation_rows": q, "samples": pc.shape[1], "native_rows": pc.shape[0] - q,
        "seed": SEED, "spectrum": spectrum.tolist(), "options": options,
        "direct_eigenvalues": direct["eigenvalues"].tolist(),
        "snapshot_eigenvalues": snapshot["eigenvalues"].tolist(),
        "comparisons": [_comparison(pc, weights, direct, snapshot, n, q) for n in (1, 3, 4, 6)],
    }


def verify_curve() -> dict:
    payload, native, query_native = _fixture()
    rows = payload["rows"]
    h = curve_rows(native, rows, 0, rows)
    hmean, umean = h.mean(axis=1, keepdims=True), native.mean(axis=1, keepdims=True)
    pc = np.vstack([h - hmean, native - umean])
    weights = np.r_[np.full(rows, 1 / rows), np.zeros(native.shape[0])]
    direct = direct_decompose(pc, weights, payload["options"])
    snapshot = snapshot_decompose(pc, weights, payload["options"])
    query = curve_rows(query_native, rows, 0, rows) - hmean
    query_centered_native = query_native - umean
    comparisons = []
    for n in (1, 2, 3, 5, 7, 9):
        item = _comparison(pc, weights, direct, snapshot, n, rows)
        zs, zd = snapshot["modes"][:, :n], direct["modes"][:, :n]
        xs, xd = zs[:rows].T @ (query / rows), zd[:rows].T @ (query / rows)
        us, ud = umean + zs[rows:] @ xs, umean + zd[rows:] @ xd
        regenerated = curve_rows(us, rows, 0, rows) - hmean
        regenerated_direct = curve_rows(ud, rows, 0, rows) - hmean
        modal = zs[:rows] @ xs
        item.update({
            "retained_variance_fraction": float(snapshot["eigenvalues"][:n].sum() / snapshot["info"]["total_variance"]),
            "relative_audit_native_error": float(np.linalg.norm(query_native - us) / np.linalg.norm(query_centered_native)),
            "relative_audit_modal_error": _relative(modal, query),
            "relative_audit_regenerated_error": _relative(regenerated, query),
            "relative_direct_snapshot_regenerated_difference": _relative(regenerated, regenerated_direct),
            "out_of_bounds_designs": int(np.count_nonzero(np.any((us < -1 - 1e-12) | (us > 1 + 1e-12), axis=0))),
        })
        if item["relative_direct_snapshot_regenerated_difference"] > 1e-9:
            raise AssertionError("Direct and snapshot regenerated geometries differ")
        comparisons.append(item)

    # A genuine row-provider fit must agree with the resident-data solver.
    streamed = fit_streaming(
        lambda start, stop: curve_rows(native, rows, start, stop),
        (rows, native.shape[1]),
        lambda start, stop: np.full(stop - start, 1 / rows),
        native, {**payload["options"], "block_rows": 31}, ci=payload["ci"],
    )
    n = payload["selected_modes"]
    if streamed["nconf"] != n:
        raise AssertionError("The curve confidence target must select six complete modes")
    streamed_coordinates = transform_streaming(
        streamed,
        lambda start, stop: curve_rows(native, rows, start, stop),
        lambda start, stop: curve_rows(query_native, rows, start, stop),
        query_native.shape[1], lambda start, stop: np.full(stop - start, 1 / rows),
    )
    streamed_backmap = backmap_streaming(streamed, streamed_coordinates)
    dense_coordinates = (snapshot["modes"][:rows, :n].T @ (query / rows)).T
    dense_backmap = umean + snapshot["modes"][rows:, :n] @ dense_coordinates.T
    np.testing.assert_allclose(streamed_backmap, dense_backmap, rtol=1e-10, atol=1e-12)
    return {
        "fixture": str(FIXTURE.relative_to(ROOT)), "generator": payload["generator"],
        "observation_rows": rows, "construction_samples": native.shape[1],
        "audit_samples": query_native.shape[1], "native_rows": native.shape[0],
        "metric": "uniform 1/Q", "domain": [-1.0, 1.0], "domain_tolerance": 1e-12,
        "options": payload["options"], "comparisons": comparisons,
        "streamed": {
            "block_rows": 31, "selected_modes": n, "ci": payload["ci"],
            "relative_audit_backmap_difference": _relative(streamed_backmap, dense_backmap),
            "max_relative_eigenvalue_difference": float(np.max(np.abs(streamed["eigenvalues"] - snapshot["eigenvalues"]) / snapshot["eigenvalues"])),
        },
        "eigenvalues": snapshot["eigenvalues"].tolist(),
    }


def verify_conditioning() -> dict:
    results = []
    for decades in (2, 6, 10, 12, 14):
        spectrum = np.logspace(0, -decades, 6)
        pc, weights, q = _prescribed_data(spectrum)
        options = {"eig_rtol": 0.0, "eig_atol": 0.0, "block_rows": 31}
        snapshot = snapshot_decompose(pc, weights, options)
        direct = direct_decompose(pc, weights, options)
        rank = snapshot["eigenvalues"].size
        native_reconstruction = snapshot["modes"][q:] @ snapshot["coordinates"].T
        results.append({
            "spectral_decades": decades,
            "expected_positive_eigenvalues": spectrum.tolist(),
            "snapshot_eigenvalues": snapshot["eigenvalues"].tolist(),
            "direct_eigenvalues": direct["eigenvalues"].tolist(),
            "snapshot_resolved_rank": rank,
            "direct_resolved_rank": direct["eigenvalues"].size,
            "effective_relative_cutoff": snapshot["info"]["eig_rtol"],
            "absolute_eigenvalue_threshold": snapshot["info"]["eigenvalue_threshold"],
            "max_relative_resolved_eigenvalue_error": float(np.max(np.abs(snapshot["eigenvalues"] - spectrum[:rank]) / spectrum[:rank])),
            "relative_full_native_reconstruction_error": _relative(native_reconstruction, pc[q:]),
        })
    return {
        "purpose": "Measure conditioning and rank truncation; full native error includes discarded directions.",
        "results": results,
    }


def verify_large(rows: int) -> dict:
    payload, native, query_native = _fixture()
    if rows < payload["rows"]:
        raise ValueError("Large-case resolution must be at least the reference resolution")
    samples, native_rows = native.shape[1], native.shape[0]
    stats = {"calls": 0, "largest_rows_requested": 0}

    def reader(start: int, stop: int) -> np.ndarray:
        stats["calls"] += 1
        stats["largest_rows_requested"] = max(stats["largest_rows_requested"], stop - start)
        return curve_rows(native, rows, start, stop)

    def weights(start: int, stop: int) -> np.ndarray:
        return np.full(stop - start, 1 / rows)

    initial_rss = _rss_bytes()
    start = time.perf_counter()
    model = fit_streaming(reader, (rows, samples), weights, native, payload["options"], ci=payload["ci"])
    fit_seconds = time.perf_counter() - start
    fit_rss = _rss_bytes()
    fit_calls = stats["calls"]
    if model["nconf"] != payload["selected_modes"]:
        raise AssertionError("The large curve case must retain six modes")
    start = time.perf_counter()
    query_coordinates = transform_streaming(
        model, reader,
        lambda begin, end: curve_rows(query_native, rows, begin, end),
        query_native.shape[1], weights,
    )
    query_backmap = backmap_streaming(model, query_coordinates)
    construction_backmap = backmap_streaming(model, model["coordinates"])
    query_seconds = time.perf_counter() - start
    final_rss = _rss_bytes()

    # These midpoint sine functions have the same discrete inner products for
    # either resolution. A small resident-data calculation provides the oracle.
    small_rows = payload["rows"]
    h = curve_rows(native, small_rows, 0, small_rows)
    hm, um = h.mean(axis=1, keepdims=True), native.mean(axis=1, keepdims=True)
    pc = np.vstack([h - hm, native - um])
    reference = snapshot_decompose(
        pc, np.r_[np.full(small_rows, 1 / small_rows), np.zeros(native_rows)], payload["options"]
    )
    n = model["nconf"]
    expected_construction = um + reference["modes"][small_rows:, :n] @ reference["coordinates"][:, :n].T
    query = curve_rows(query_native, small_rows, 0, small_rows) - hm
    ref_query_coordinates = reference["modes"][:small_rows, :n].T @ (query / small_rows)
    expected_query = um + reference["modes"][small_rows:, :n] @ ref_query_coordinates
    np.testing.assert_allclose(model["eigenvalues"], reference["eigenvalues"], rtol=1e-9, atol=1e-13)
    np.testing.assert_allclose(construction_backmap, expected_construction, rtol=1e-9, atol=1e-11)
    np.testing.assert_allclose(query_backmap, expected_query, rtol=1e-9, atol=1e-11)
    if stats["largest_rows_requested"] > payload["block_rows"]:
        raise AssertionError("The streaming API exceeded the configured row-block limit")
    return {
        "observation_rows": rows, "samples": samples, "native_rows": native_rows,
        "audit_samples": query_native.shape[1], "selected_modes": n, "ci": payload["ci"],
        "block_rows": payload["block_rows"], "native_only": True,
        "fit_provider_calls": fit_calls,
        "query_training_provider_calls": stats["calls"] - fit_calls,
        "largest_rows_requested": stats["largest_rows_requested"],
        "fit_seconds": fit_seconds, "cross_gram_query_seconds": query_seconds,
        "initial_process_peak_rss_bytes": initial_rss,
        "fit_process_peak_rss_bytes": fit_rss,
        "fit_and_query_process_peak_rss_bytes": final_rss,
        "memory_method": "Separate process; getrusage(RUSAGE_SELF).ru_maxrss. Peaks include interpreter, libraries, native inputs, solver workspace and temporaries; sampled before the small reference calculation.",
        "analytic_array_bytes": {
            "augmented_direct_operator": (rows + native_rows)**2 * 8,
            "observation_direct_covariance": rows**2 * 8,
            "complete_observation_snapshots": rows * samples * 8,
            "sample_gram": samples**2 * 8,
            "one_observation_block": min(payload["block_rows"], rows) * samples * 8,
        },
        "eigenvalues": model["eigenvalues"].tolist(),
        "total_variance": model["info"]["total_variance"],
        "achieved_ci": model["info"]["achieved_ci"],
        "max_relative_eigenvalue_difference_to_small_reference": float(np.max(np.abs(model["eigenvalues"] - reference["eigenvalues"]) / reference["eigenvalues"])),
        "relative_construction_backmap_difference_to_small_reference": _relative(construction_backmap, expected_construction),
        "relative_audit_backmap_difference_to_small_reference": _relative(query_backmap, expected_query),
        "construction_backmap": construction_backmap.tolist(),
        "query_backmap": query_backmap.tolist(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "benchmarks" / "results" / "snapshot_manuscript.json")
    parser.add_argument("--large-rows", type=int, default=1048576)
    parser.add_argument("--skip-large", action="store_true")
    parser.add_argument("--large-worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.large_worker:
        result = verify_large(args.large_rows)
    else:
        started = time.perf_counter()
        result = {
            "schema_version": 1,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "scope": "Controlled toolkit experiments; historical manuscript outputs are not used as numerical references.",
            "environment": _environment(),
            "prescribed_spectrum": verify_prescribed(),
            "geometric_audit": verify_curve(),
            "conditioning": verify_conditioning(),
        }
        if not args.skip_large:
            with tempfile.TemporaryDirectory(prefix="pme-snapshot-verification-") as directory:
                child_output = Path(directory) / "large.json"
                subprocess.run(
                    [sys.executable, str(Path(__file__).resolve()), "--large-worker", "--large-rows", str(args.large_rows), "--output", str(child_output)],
                    check=True, env=os.environ.copy(),
                )
                result["large_streamed_case"] = json.loads(child_output.read_text(encoding="utf-8"))
        result["elapsed_seconds"] = time.perf_counter() - started
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Snapshot verification passed: {args.output}")


if __name__ == "__main__":
    main()
