from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .model import PmeModel


@dataclass
class _Source:
    name: str
    type: str
    group: str
    cond: int
    nCond: int
    rows: np.ndarray


def _mode_str(model: PmeModel) -> str:
    return str(model.mode).lower()


def _mact(model: PmeModel) -> int:
    return int(model.uinfo["Mact"])


def _field_k(item: dict[str, Any]) -> int:
    disc = item.get("disc", {})
    if isinstance(disc, dict) and disc.get("K") is not None:
        return int(disc["K"])

    patches = disc.get("patches", []) if isinstance(disc, dict) else []
    if patches:
        return int(sum(int(p["K"]) for p in patches))

    raise ValueError("Field discretization must define disc.K or disc.patches")


def _kplot(model: PmeModel) -> int:
    lam = np.asarray(model.eigvals_full, dtype=float).reshape(-1)
    return int(min(_mact(model), lam.size))


def _p_blocks(model: PmeModel) -> dict[str, np.ndarray]:
    """
    Build P-space row positions for D/U/F/C consistently with the current mode.
    Mirrors the logic used in MATLAB plotting/report helper code.
    """
    layout = model.layout
    mode = _mode_str(model)
    mact = _mact(model)
    np_rows = int(model.z_reduced.shape[0])

    pos: dict[str, np.ndarray] = {
        "D": np.array([], dtype=int),
        "U": np.array([], dtype=int),
        "F": np.array([], dtype=int),
        "C": np.array([], dtype=int),
    }

    if mode == "pme":
        d0 = int(layout["D"]["nRows"])
        pos["D"] = np.arange(0, d0, dtype=int)
        pos["U"] = np.arange(d0, d0 + mact, dtype=int)

    elif mode == "pi":
        r = 0
        drows = int(layout["D"]["nRows"])
        pos["D"] = np.arange(r, r + drows, dtype=int)
        r += drows

        pos["U"] = np.arange(r, r + mact, dtype=int)
        r += mact

        if int(layout.get("F", {}).get("nRows", 0)) > 0:
            frows = int(layout["F"]["nRows"])
            pos["F"] = np.arange(r, r + frows, dtype=int)
            r += frows

        if int(layout.get("C", {}).get("nRows", 0)) > 0:
            crows = int(layout["C"]["nRows"])
            pos["C"] = np.arange(r, r + crows, dtype=int)

    elif mode == "pd":
        r = 0
        pos["U"] = np.arange(r, r + mact, dtype=int)
        r += mact

        if int(layout.get("F", {}).get("nRows", 0)) > 0:
            frows = int(layout["F"]["nRows"])
            pos["F"] = np.arange(r, r + frows, dtype=int)
            r += frows

        if int(layout.get("C", {}).get("nRows", 0)) > 0:
            crows = int(layout["C"]["nRows"])
            pos["C"] = np.arange(r, r + crows, dtype=int)

    else:
        raise ValueError(f"Unknown mode: {mode}")

    for key in ("D", "U", "F", "C"):
        rr = pos[key]
        pos[key] = rr[(rr >= 0) & (rr < np_rows)]

    return pos


def _build_info_sources(model: PmeModel) -> list[_Source]:
    """
    Python port of the MATLAB helper that builds information sources:
    - geom counts as 1 source when present (PME, PI-PME)
    - each field condition counts as 1 source
    - each scalar condition counts as 1 source
    """
    layout = model.layout
    mode = _mode_str(model)
    pos = _p_blocks(model)

    sources: list[_Source] = []

    if mode in ("pme", "pi") and pos["D"].size > 0:
        sources.append(
            _Source(
                name="geom",
                type="geom",
                group="geom",
                cond=1,
                nCond=1,
                rows=pos["D"],
            )
        )

    if pos["F"].size > 0:
        offset = 0
        items = list(layout.get("F", {}).get("items", []) or [])
        if items:
            for item in items:
                name = str(item.get("name", "field"))
                n_cond = int(item.get("nCond", 1))
                n_rows = int(item.get("nRows", 0))
                k = int(n_rows // max(n_cond, 1))

                for ic in range(n_cond):
                    rows = pos["F"][offset + ic * k : offset + (ic + 1) * k]
                    sources.append(
                        _Source(
                            name=name if n_cond == 1 else f"{name}_{ic+1}",
                            type="field",
                            group=name,
                            cond=ic + 1,
                            nCond=n_cond,
                            rows=np.asarray(rows, dtype=int),
                        )
                    )
                offset += n_rows
        else:
            sources.append(
                _Source(
                    name="field",
                    type="field",
                    group="field",
                    cond=1,
                    nCond=1,
                    rows=pos["F"],
                )
            )

    if pos["C"].size > 0:
        offset = 0
        items = list(layout.get("C", {}).get("items", []) or [])
        if items:
            for item in items:
                name = str(item.get("name", "scalar"))
                n_cond = int(item.get("nCond", 1))
                for ic in range(n_cond):
                    rows = pos["C"][offset + ic : offset + ic + 1]
                    sources.append(
                        _Source(
                            name=name if n_cond == 1 else f"{name}_{ic+1}",
                            type="scalar",
                            group=name,
                            cond=ic + 1,
                            nCond=n_cond,
                            rows=np.asarray(rows, dtype=int),
                        )
                    )
                offset += n_cond
        else:
            for j, rr in enumerate(pos["C"]):
                sources.append(
                    _Source(
                        name=f"scalar_{j+1}",
                        type="scalar",
                        group="scalar",
                        cond=j + 1,
                        nCond=int(pos["C"].size),
                        rows=np.asarray([rr], dtype=int),
                    )
                )

    return sources


def _reconstruction_curves(model: PmeModel) -> dict[str, Any]:
    """
    Build the same reconstruction diagnostics used by MATLAB report/plots:
    - var_src
    - nmse_t
    - var_t
    - var_p
    - nmse_global
    - ev_global
    - lam_cum_ninf
    """
    sources = _build_info_sources(model)
    ninf = len(sources)
    kplot = _kplot(model)

    if ninf == 0:
        return {
            "enable": False,
            "k_grid": np.arange(1, kplot + 1, dtype=int),
            "sources": [],
            "var_src": np.zeros((0,), dtype=float),
            "nmse_t": np.zeros((0, kplot), dtype=float),
            "var_t": np.zeros((0, kplot), dtype=float),
            "var_p": np.zeros((0, kplot), dtype=float),
            "nmse_global": np.zeros((kplot,), dtype=float),
            "ev_global": np.zeros((kplot,), dtype=float),
            "lam_cum_ninf": np.zeros((kplot,), dtype=float),
        }

    pc = np.asarray(model.pc, dtype=float)
    z_full = np.asarray(model.z_full, dtype=float)
    ak_full = np.asarray(model.ak_full, dtype=float)

    var_src = np.zeros((ninf,), dtype=float)
    for i, src in enumerate(sources):
        rr = src.rows
        var_src[i] = float(np.sum(np.var(pc[rr, :], axis=1, ddof=0)))

    nmse_t = np.zeros((ninf, kplot), dtype=float)

    for jconf in range(1, kplot + 1):
        k = jconf
        prec = z_full[:, :k] @ ak_full[:, :k].T
        e = pc - prec

        for i, src in enumerate(sources):
            rr = src.rows
            mse_block = float(np.mean(np.sum(e[rr, :] ** 2, axis=0)))
            nmse_t[i, jconf - 1] = mse_block / max(var_src[i], np.finfo(float).eps)

    var_t = 1.0 - nmse_t

    var_p = np.zeros_like(var_t)
    if kplot >= 1:
        var_p[:, 0] = var_t[:, 0]
    if kplot >= 2:
        var_p[:, 1:] = var_t[:, 1:] - var_t[:, :-1]

    nmse_global = np.mean(nmse_t, axis=0)
    ev_global = 1.0 - nmse_global

    lam = np.asarray(model.eigvals_full, dtype=float).reshape(-1)
    lam_cum = np.cumsum(lam[:kplot]) / max(float(ninf), np.finfo(float).eps)

    return {
        "enable": True,
        "k_grid": np.arange(1, kplot + 1, dtype=int),
        "sources": sources,
        "var_src": np.real(var_src),
        "nmse_t": np.real(nmse_t),
        "var_t": np.real(var_t),
        "var_p": np.real(var_p),
        "nmse_global": np.real(nmse_global),
        "ev_global": np.real(ev_global),
        "lam_cum_ninf": np.real(lam_cum),
    }


def _variance_summary(model: PmeModel) -> dict[str, Any]:
    """
    Sanity-check variance summary, close to MATLAB report style.
    """
    mode = _mode_str(model)
    stats = dict(model.stats_w)

    out: dict[str, Any] = {
        "mode": mode,
        "var_total": np.nan,
        "var_geom": np.nan,
        "var_vars": np.nan,
        "rows_geom": int(model.layout["D"]["nRows"]),
        "rows_vars": int(model.uinfo["Mact"]),
    }

    if "varD" in stats:
        out["var_geom"] = float(stats["varD"])
    if "varU" in stats:
        out["var_vars"] = float(stats["varU"])

    if mode == "pme":
        vg = float(out["var_geom"])
        vu = float(out["var_vars"])
        out["var_total"] = vg + vu
        return out

    # For PI / PD, build a fuller summary from model.pc and P-space positions
    pos = _p_blocks(model)
    pc = np.asarray(model.pc, dtype=float)

    if pos["D"].size > 0:
        out["var_geom"] = float(np.sum(np.var(pc[pos["D"], :], axis=1, ddof=0)))
    if pos["U"].size > 0:
        out["var_vars"] = float(np.sum(np.var(pc[pos["U"], :], axis=1, ddof=0)))

    var_f = float(np.sum(np.var(pc[pos["F"], :], axis=1, ddof=0))) if pos["F"].size > 0 else 0.0
    var_c = float(np.sum(np.var(pc[pos["C"], :], axis=1, ddof=0))) if pos["C"].size > 0 else 0.0

    out["var_fields"] = var_f
    out["var_scalars"] = var_c
    out["rows_fields"] = int(pos["F"].size)
    out["rows_scalars"] = int(pos["C"].size)

    parts = []
    for key in ("var_geom", "var_vars"):
        val = out.get(key, np.nan)
        if np.isfinite(val):
            parts.append(float(val))
    parts.extend([var_f, var_c])

    out["var_total"] = float(np.sum(parts))
    return out


def build_report(model: PmeModel) -> dict[str, Any]:
    """
    Build a complete report dictionary for PME / PI-PME / PD-PME.
    """
    mode = _mode_str(model)
    var = _variance_summary(model)
    rec = _reconstruction_curves(model)

    k = int(model.nconf)
    krep = min(k, len(rec["k_grid"])) if len(rec["k_grid"]) > 0 else 1
    krep0 = krep - 1

    mact = int(model.uinfo["Mact"])
    reduction_pct = 100.0 * (1.0 - float(k) / float(mact))

    nmse_at_nconf = {}
    for i, src in enumerate(rec["sources"]):
        nmse_at_nconf[str(src.name)] = float(rec["nmse_t"][i, krep0])

    rep: dict[str, Any] = {
        "mode": mode,
        "S": int(model.db_used_shape[1]),
        "Mact": mact,
        "CI": float(model.cfg["CI"]),
        "variance": var,
        "nconf": int(model.nconf),
        "reduction_pct": reduction_pct,
        "ninfo": int(model.stats_w["ninfo"]["total"]),
        "nmse": {
            "k_grid": np.asarray(rec["k_grid"], dtype=int),
            "sources": [
                {
                    "name": s.name,
                    "type": s.type,
                    "group": s.group,
                    "cond": s.cond,
                    "nCond": s.nCond,
                    "rows": np.asarray(s.rows, dtype=int),
                }
                for s in rec["sources"]
            ],
            "var_src": np.asarray(rec["var_src"], dtype=float),
            "nmse_t": np.asarray(rec["nmse_t"], dtype=float),
            "var_t": np.asarray(rec["var_t"], dtype=float),
            "var_p": np.asarray(rec["var_p"], dtype=float),
            "nmse_at_nconf": nmse_at_nconf,
        },
        "global_check": {
            "nmse_global": np.asarray(rec["nmse_global"], dtype=float),
            "ev_global": np.asarray(rec["ev_global"], dtype=float),
            "lam_cum_ninf": np.asarray(rec["lam_cum_ninf"], dtype=float),
            "one_minus_mean_nmse": float(rec["ev_global"][krep0]) if len(rec["ev_global"]) else np.nan,
            "eig_ratio": float(rec["lam_cum_ninf"][krep0]) if len(rec["lam_cum_ninf"]) else np.nan,
            "diff": (
                float(rec["ev_global"][krep0] - rec["lam_cum_ninf"][krep0])
                if len(rec["ev_global"])
                else np.nan
            ),
        },
        "filters": dict(model.filter_info),
        "weights": dict(model.stats_w),
        "kplot": int(len(rec["k_grid"])),
        "krep": int(krep),
    }

    return rep


def print_report(model: PmeModel) -> dict[str, Any]:
    """
    Print MATLAB-style textual report and return the report dictionary.
    """
    rep = build_report(model)

    mode = str(rep["mode"])
    s = int(rep["S"])
    mact = int(rep["Mact"])
    ci = float(rep["CI"])
    nconf = int(rep["nconf"])
    reduction_pct = float(rep["reduction_pct"])
    ninfo = int(rep["ninfo"])
    kplot = int(rep["kplot"])
    krep = int(rep["krep"])

    var = rep["variance"]
    var_total = float(var["var_total"])

    print()
    print("[pme.report] ===== SANITY CHECK: variance by component =====")
    print(f"[pme.report] mode={mode}, S={s}, Mact={mact}, CI={ci:.4f}")
    print(f"[pme.report] var_total   = {var_total:.6e}")

    if np.isfinite(var.get("var_geom", np.nan)):
        print(
            f"[pme.report] var_geom    = {float(var['var_geom']):.6e} "
            f"(rows={int(var.get('rows_geom', 0))})"
        )

    if np.isfinite(var.get("var_vars", np.nan)):
        print(
            f"[pme.report] var_vars    = {float(var['var_vars']):.6e} "
            f"(rows={int(var.get('rows_vars', 0))})"
        )

    if "var_fields" in var:
        print(
            f"[pme.report] var_fields  = {float(var['var_fields']):.6e} "
            f"(rows={int(var.get('rows_fields', 0))})"
        )

    if "var_scalars" in var:
        print(
            f"[pme.report] var_scalars = {float(var['var_scalars']):.6e} "
            f"(rows={int(var.get('rows_scalars', 0))})"
        )

    print()
    print("[pme.report] ===== DIMENSIONALITY REDUCTION RESULT =====")
    print(f"[pme.report] N modes needed for CI={ci:.4f}: {nconf}")
    print(
        f"[pme.report] reduced from Mact={mact} to N={nconf}  ->  {reduction_pct:.2f} % reduction"
    )
    print(f"[pme.report] number of information sources = {ninfo}")

    print()
    print("[pme.report] ===== NMSE (per information source) =====")
    print(f"[pme.report] k-grid = 1..kplot (printed: k=nconf)")

    for src_name, value in rep["nmse"]["nmse_at_nconf"].items():
        print(f"[pme.report] NMSE {str(src_name):<16} = {float(value):.9f}")

    one_minus_mean_nmse = float(rep["global_check"]["one_minus_mean_nmse"])
    eig_ratio = float(rep["global_check"]["eig_ratio"])
    diff = float(rep["global_check"]["diff"])

    print()
    print("[pme.report] ===== GLOBAL CHECK (W-consistent) =====")
    print(f"[pme.report] 1 - mean(NMSE_i) at k=nconf = {one_minus_mean_nmse:.6f}")
    print(f"[pme.report] sum(lambda_1..k)/ninf at k=nconf = {eig_ratio:.6f}")
    print(f"[pme.report] diff = {diff:.2e}")

    return rep
