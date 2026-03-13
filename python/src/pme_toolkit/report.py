from __future__ import annotations

from typing import Any

import numpy as np

from .model import PmeModel


def _nmse_geom_by_k(model: PmeModel) -> np.ndarray:
    """Compute geometry NMSE as a function of retained modes k=1..nconf.

    For PME the geometry block is the first D rows of P.
    NMSE is computed on the centered fluctuations Pc, consistently with the
    dimensionality-reduction report logic used in MATLAB.
    """
    pc = model.pc
    dlen = int(model.layout["D"]["nRows"])
    pc_geom = pc[:dlen, :]

    denom = float(np.mean(np.sum(pc_geom**2, axis=0)))
    if denom <= 0.0:
        return np.zeros(model.nconf, dtype=float)

    nmse = np.zeros(model.nconf, dtype=float)

    for k in range(1, model.nconf + 1):
        zk = model.z_full[:, :k]
        ak = pc.T @ model.w @ zk
        pc_hat = zk @ ak.T
        err = pc_geom - pc_hat[:dlen, :]
        nmse[k - 1] = float(np.mean(np.sum(err**2, axis=0)) / denom)

    return nmse


def _variance_summary(model: PmeModel) -> dict[str, float]:
    """Return total/geometry/variables variance for PME."""
    var_d = float(model.stats_w.get("varD", np.nan))
    var_u = float(model.stats_w.get("varU", np.nan))
    var_total = var_d + var_u
    return {
        "var_total": var_total,
        "var_geom": var_d,
        "var_vars": var_u,
    }


def build_report(model: PmeModel) -> dict[str, Any]:
    """Build a report dictionary for the current model."""
    if model.mode != "pme":
        raise NotImplementedError("build_report currently supports only PME")

    var = _variance_summary(model)
    nmse_geom = _nmse_geom_by_k(model)

    k = model.nconf
    nmse_geom_k = float(nmse_geom[k - 1])

    # For PME there is one information source: geometry only
    one_minus_mean_nmse = 1.0 - nmse_geom_k

    ninfo = int(model.stats_w["ninfo"]["total"])
    eig_ratio = float(np.sum(model.eigvals_reduced[:k]) / max(ninfo, 1))
    diff = one_minus_mean_nmse - eig_ratio

    mact = int(model.uinfo["Mact"])
    reduction_pct = 100.0 * (1.0 - float(k) / float(mact))

    rep: dict[str, Any] = {
        "mode": model.mode,
        "S": int(model.db_used_shape[1]),
        "Mact": mact,
        "CI": float(model.cfg["CI"]),
        "variance": var,
        "nconf": int(model.nconf),
        "reduction_pct": reduction_pct,
        "ninfo": ninfo,
        "nmse": {
            "geom_by_k": nmse_geom,
            "geom_at_nconf": nmse_geom_k,
        },
        "global_check": {
            "one_minus_mean_nmse": one_minus_mean_nmse,
            "eig_ratio": eig_ratio,
            "diff": diff,
        },
        "filters": dict(model.filter_info),
        "weights": dict(model.stats_w),
    }

    return rep


def print_report(model: PmeModel) -> dict[str, Any]:
    """Print a MATLAB-style textual report and return the report dictionary."""
    rep = build_report(model)

    d_rows = int(model.layout["D"]["nRows"])
    mact = int(model.uinfo["Mact"])
    ci = float(rep["CI"])
    s = int(rep["S"])

    var_total = float(rep["variance"]["var_total"])
    var_geom = float(rep["variance"]["var_geom"])
    var_vars = float(rep["variance"]["var_vars"])

    nconf = int(rep["nconf"])
    reduction_pct = float(rep["reduction_pct"])
    ninfo = int(rep["ninfo"])

    nmse_geom = float(rep["nmse"]["geom_at_nconf"])
    one_minus_mean_nmse = float(rep["global_check"]["one_minus_mean_nmse"])
    eig_ratio = float(rep["global_check"]["eig_ratio"])
    diff = float(rep["global_check"]["diff"])

    print()
    print("[pme.report] ===== SANITY CHECK: variance by component =====")
    print(f"[pme.report] mode={model.mode}, S={s}, Mact={mact}, CI={ci:.4f}")
    print(f"[pme.report] var_total   = {var_total:.6e}")
    print(f"[pme.report] var_geom    = {var_geom:.6e} (rows={d_rows})")
    print(f"[pme.report] var_vars    = {var_vars:.6e} (rows={mact})")

    print()
    print("[pme.report] ===== DIMENSIONALITY REDUCTION RESULT =====")
    print(f"[pme.report] N modes needed for CI={ci:.4f}: {nconf}")
    print(
        f"[pme.report] reduced from Mact={mact} to N={nconf}  ->  {reduction_pct:.2f} % reduction"
    )
    print(f"[pme.report] number of information sources = {ninfo}")

    print()
    print("[pme.report] ===== NMSE (per information source) =====")
    print(f"[pme.report] k-grid = 1..nconf (printed: k=nconf)")
    print(f"[pme.report] NMSE geom             = {nmse_geom:.9f}")

    print()
    print("[pme.report] ===== GLOBAL CHECK (W-consistent) =====")
    print(f"[pme.report] 1 - mean(NMSE_i) at k=nconf = {one_minus_mean_nmse:.6f}")
    print(f"[pme.report] sum(lambda_1..k)/ninf at k=nconf = {eig_ratio:.6f}")
    print(f"[pme.report] diff = {diff:.2e}")

    return rep
