from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.linalg import eig

from .config_loader import load_case_json
from .io import load_mat_database, load_mat_range
from .layout import parse_layout


Array = NDArray[np.float64]


def _defaults(cfg: dict[str, Any]) -> dict[str, Any]:
    out = dict(cfg)

    out.setdefault("mode", "pme")
    out.setdefault("CI", 0.95)
    out.setdefault("baseline_col", 0)

    out.setdefault("filters", {})
    out.setdefault("io", {})
    out.setdefault("phys", {})
    out.setdefault("geom", {})
    out.setdefault("vars", {})

    out["phys"].setdefault("fields", [])
    out["phys"].setdefault("scalars", [])
    out["filters"].setdefault("remove_nan", True)

    return out


def _choose_nconf(eigvals: Array, ci: float) -> int:
    cum = np.cumsum(eigvals)
    tot = float(cum[-1]) if eigvals.size > 0 else 0.0
    if tot <= 0.0:
        return 1
    ratio = cum / tot
    idx = int(np.searchsorted(ratio, ci, side="left"))
    return min(idx + 1, eigvals.size)


def _slice_blocks(db: Array, layout: dict[str, Any]) -> dict[str, Array]:
    if db.shape[0] < int(layout["totalRows"]):
        raise ValueError(
            f"DB has {db.shape[0]} rows but layout expects at least {layout['totalRows']}"
        )

    d_slice = layout["D"]["rows"]
    u_slice = layout["Ubase"]["rows"]
    f_slice = layout["F"]["rows"]
    c_slice = layout["C"]["rows"]

    return {
        "D": np.asarray(db[d_slice, :], dtype=float),
        "Ubase": np.asarray(db[u_slice, :], dtype=float),
        "F": np.asarray(db[f_slice, :], dtype=float)
        if layout["F"]["nRows"] > 0
        else np.zeros((0, db.shape[1]), dtype=float),
        "C": np.asarray(db[c_slice, :], dtype=float)
        if layout["C"]["nRows"] > 0
        else np.zeros((0, db.shape[1]), dtype=float),
    }


def _convert_idx_active(
    idx_active: list[int] | tuple[int, ...] | Array | None,
    mbase: int,
) -> Array:
    if idx_active is None or len(idx_active) == 0:
        return np.arange(mbase, dtype=int)

    idx = np.asarray(idx_active, dtype=int).ravel()

    # JSON / repository convention is 0-based.
    # If the user passed 1-based manually, convert only when there is no zero
    # and all indices are in 1..Mbase.
    if np.min(idx) >= 1 and np.max(idx) <= mbase:
        idx = idx - 1

    if np.any(idx < 0) or np.any(idx >= mbase):
        raise ValueError("idx_active contains out-of-range entries")

    _, unique_pos = np.unique(idx, return_index=True)
    idx = idx[np.sort(unique_pos)]
    return idx.astype(int)


def _prepare_vars(
    ubase: Array,
    cfg: dict[str, Any],
    urange_full: Array | None,
) -> tuple[Array, dict[str, Any]]:
    vars_cfg = dict(cfg.get("vars", {}) or {})
    mbase = int(vars_cfg["Mbase"])

    if ubase.shape[0] != mbase:
        raise ValueError(f"Ubase has {ubase.shape[0]} rows but cfg.vars.Mbase={mbase}")

    idx_active = _convert_idx_active(vars_cfg.get("idx_active", []), mbase)
    idx_fixed = np.array(
        [i for i in range(mbase) if i not in set(idx_active.tolist())],
        dtype=int,
    )

    uraw_act = ubase[idx_active, :]

    if urange_full is None:
        if bool(vars_cfg.get("use_db_range_if_missing", False)):
            urange_full = np.column_stack(
                [np.min(ubase, axis=1), np.max(ubase, axis=1)]
            )
            urange_source = "db"
        else:
            urange_source = "missing"
    else:
        urange_source = "user"

    if urange_full is None:
        return uraw_act.copy(), {
            "idx_active": idx_active,
            "idx_fixed": idx_fixed,
            "Mact": int(idx_active.size),
            "Mbase": mbase,
            "Urange": None,
            "Urange_full": None,
            "Urange_source": urange_source,
        }

    urange_full = np.asarray(urange_full, dtype=float)
    if urange_full.ndim != 2 or urange_full.shape[1] != 2:
        raise ValueError(f"Urange must be [M x 2], got shape {urange_full.shape}")

    if urange_full.shape[0] == mbase:
        pass
    elif urange_full.shape[0] == idx_active.size:
        expanded = np.full((mbase, 2), np.nan, dtype=float)
        expanded[idx_active, :] = urange_full
        urange_full = expanded
    else:
        raise ValueError(
            f"Urange must have {mbase} or {idx_active.size} rows, got {urange_full.shape[0]}"
        )

    urange_act = urange_full[idx_active, :]
    umin = urange_act[:, [0]]
    umax = urange_act[:, [1]]
    denom = np.maximum(umax - umin, np.finfo(float).eps)

    uact = (uraw_act - umin) / denom
    uact = np.clip(uact, 0.0, 1.0)

    return uact, {
        "idx_active": idx_active,
        "idx_fixed": idx_fixed,
        "Mact": int(idx_active.size),
        "Mbase": mbase,
        "Urange": urange_act,
        "Urange_full": urange_full,
        "Urange_source": urange_source,
        "min_after_clip": float(np.min(uact)),
        "max_after_clip": float(np.max(uact)),
    }


def _compose_p(mode: str, d: Array, uact: Array, f: Array, c: Array) -> Array:
    mode = mode.lower()

    if mode == "pme":
        return np.vstack([d, uact])

    if mode == "pi":
        raise NotImplementedError("PI-PME is not implemented yet in the Python port")

    if mode == "pd":
        raise NotImplementedError("PD-PME is not implemented yet in the Python port")

    raise ValueError(f"Unknown mode: {mode}")


def _baseline_col_zero_based(cfg: dict[str, Any], n_samples: int) -> int:
    bc = int(cfg.get("baseline_col", 0))
    if bc < 0 or bc >= n_samples:
        raise ValueError(f"baseline_col={bc} out of range for {n_samples} samples")
    return bc


def _apply_repository_filters(
    db: Array,
    cfg: dict[str, Any],
) -> tuple[Array, dict[str, Any], Array]:
    """Replicate the repository filtering order for the currently supported subset.

    For now this implements:
      1) remove_nan on the FULL DB (exactly like MATLAB filters.m)
    Goal/IQR are left as future extensions.

    Returns
    -------
    db_used
        Filtered DB.
    info
        Filter diagnostics.
    mask
        Boolean mask on original columns.
    """
    db = np.asarray(db, dtype=float)
    ns = db.shape[1]
    mask = np.ones(ns, dtype=bool)
    info: dict[str, Any] = {"Ns_total": int(ns)}

    filters_cfg = dict(cfg.get("filters", {}) or {})
    remove_nan = bool(filters_cfg.get("remove_nan", True))

    bc = _baseline_col_zero_based(cfg, ns)

    if remove_nan:
        in_step = int(np.sum(mask))
        ok_local = np.all(np.isfinite(db[:, mask]), axis=0)
        kept_step = int(np.sum(ok_local))

        idx = np.flatnonzero(mask)
        mask[idx[~ok_local]] = False

        # MATLAB behaviour: never drop baseline_col
        mask[bc] = True

        info["nan_enable"] = True
        info["nan_in"] = in_step
        info["nan_kept"] = kept_step
        info["nan_dropped"] = in_step - kept_step
    else:
        info["nan_enable"] = False
        info["nan_in"] = int(np.sum(mask))
        info["nan_kept"] = int(np.sum(mask))
        info["nan_dropped"] = 0
        mask[bc] = True

    # Goal and IQR are currently not implemented in Python.
    info["goal_enable"] = False
    info["iqr_enable"] = False
    info["total_kept"] = int(np.sum(mask))

    db_used = db[:, mask]
    return db_used, info, mask


def _pme_weights(delta: Array, dlen: int, ulen: int) -> tuple[Array, dict[str, Any]]:
    """Replicate MATLAB PME weights.m for mode='pme'.

    For PME:
      - geometry (D) counts as one information source
      - variables (U) are present but not weighted
    """

    n = dlen + ulen
    w = np.zeros((n, n), dtype=float)

    def invv(x: float) -> float:
        return 1.0 / max(float(x), np.finfo(float).eps)

    # geometry variance
    var_d = float(np.sum(np.var(delta[:dlen, :], axis=1, ddof=0)))

    # variables variance (diagnostic only)
    var_u = float(np.sum(np.var(delta[dlen:dlen+ulen, :], axis=1, ddof=0)))

    w_d = invv(var_d)

    # weights
    w[:dlen, :dlen] = w_d * np.eye(dlen)

    stats = {
        "mode": "pme",
        "sizes": {"D": dlen, "U": ulen, "F": 0, "C": 0},
        "ninfo": {"D": 1, "F": 0, "C": 0, "total": 1},
        "wD": w_d,
        "wU": 0.0,
        "varD": var_d,
        "varU": var_u,        # <-- new diagnostic
    }

    return w, stats


def _weighted_fit_pme(
    p: Array,
    layout: dict[str, Any],
    uinfo: dict[str, Any],
    baseline_col: int,
) -> dict[str, Array | int | dict[str, Any]]:
    s = p.shape[1]

    p0 = p[:, [baseline_col]]
    delta = p - p0
    delta_m = np.mean(delta, axis=1, keepdims=True)
    pc = delta - delta_m

    dlen = int(layout["D"]["nRows"])
    ulen = int(uinfo["Mact"])

    w, stats_w = _pme_weights(delta, dlen, ulen)

    a = (pc @ pc.T) / float(s)
    aw = a @ w

    eigvals_raw, eigvecs_raw = eig(aw)
    eigvals_raw = np.real(eigvals_raw)
    eigvecs_raw = np.real(eigvecs_raw)

    order = np.argsort(eigvals_raw)[::-1]
    l_full = np.maximum(eigvals_raw[order], 0.0)
    z_full = eigvecs_raw[:, order]

    # Normalize columns so that Z' W Z = I
    an = np.diag(z_full.T @ w @ z_full)
    an = np.sqrt(np.maximum(an, np.finfo(float).eps))
    z_full = z_full / an[None, :]

    return {
        "P0": p0,
        "delta_m": delta_m,
        "W": w,
        "statsW": stats_w,
        "L_full": l_full,
        "Z_full": z_full,
        "Pc": pc,
    }


@dataclass
class PmeModel:
    mode: str
    cfg: dict[str, Any]
    layout: dict[str, Any]
    p0: Array
    delta_m: Array
    pc: Array
    w: Array
    z_reduced: Array
    eigvals_reduced: Array
    eigvals_full: Array
    z_full: Array
    alpha_train: Array
    uinfo: dict[str, Any]
    nconf: int
    baseline_col: int
    db_used_shape: tuple[int, int]
    filter_mask: Array
    filter_info: dict[str, Any]
    stats_w: dict[str, Any]

    def transform(self, db: Array) -> Array:
        blocks = _slice_blocks(np.asarray(db, dtype=float), self.layout)
        uact, _ = _prepare_vars(blocks["Ubase"], self.cfg, self.uinfo.get("Urange_full"))
        p = _compose_p(self.mode, blocks["D"], uact, blocks["F"], blocks["C"])

        delta = p - self.p0[:, [0]]
        pc = delta - self.delta_m[:, [0]]

        alpha = pc.T @ self.w @ self.z_reduced
        return np.asarray(alpha, dtype=float)

    def inverse_active(self, alpha: Array) -> Array:
        alpha = np.asarray(alpha, dtype=float)
        alpha = np.atleast_2d(alpha)
        if alpha.shape[1] != self.nconf:
            raise ValueError(f"alpha must have {self.nconf} columns")

        p_hat = self.p0[:, [0]] + self.delta_m[:, [0]] + self.z_reduced @ alpha.T

        d_rows = int(self.layout["D"]["nRows"])
        u_rows = int(self.uinfo["Mact"])
        start = d_rows
        stop = d_rows + u_rows

        uact = p_hat[start:stop, :].T
        return np.asarray(uact, dtype=float)

    def inverse_full(self, alpha: Array) -> Array:
        uact = self.inverse_active(alpha)
        idx_active = np.asarray(self.uinfo["idx_active"], dtype=int)
        mbase = int(self.uinfo["Mbase"])

        urange = self.uinfo.get("Urange")
        if urange is None:
            raise RuntimeError("Cannot reconstruct full variables without Urange")

        umin = urange[:, 0]
        umax = urange[:, 1]
        denom = np.maximum(umax - umin, np.finfo(float).eps)

        uact_raw = umin[None, :] + uact * denom[None, :]

        out = np.zeros((uact_raw.shape[0], mbase), dtype=float)
        out[:, idx_active] = uact_raw
        return out


def fit_pme(
    db: Array,
    cfg: dict[str, Any],
    *,
    urange_full: Array | None = None,
) -> PmeModel:
    cfg = _defaults(cfg)
    mode = str(cfg["mode"]).lower()

    if mode != "pme":
        raise NotImplementedError(
            "This Python port currently supports only PME. "
            "PI-PME and PD-PME remain TODO."
        )

    layout = parse_layout(cfg)
    db = np.asarray(db, dtype=float)

    # IMPORTANT: MATLAB filters on the FULL DB before slicing blocks.
    db_used, filter_info, filter_mask = _apply_repository_filters(db, cfg)

    blocks = _slice_blocks(db_used, layout)
    uact, uinfo = _prepare_vars(blocks["Ubase"], cfg, urange_full)
    p = _compose_p(mode, blocks["D"], uact, blocks["F"], blocks["C"])

    baseline_col = _baseline_col_zero_based(cfg, p.shape[1])

    weighted = _weighted_fit_pme(p, layout, uinfo, baseline_col)

    l_full = np.asarray(weighted["L_full"], dtype=float)
    z_full = np.asarray(weighted["Z_full"], dtype=float)
    w = np.asarray(weighted["W"], dtype=float)
    p0 = np.asarray(weighted["P0"], dtype=float)
    delta_m = np.asarray(weighted["delta_m"], dtype=float)
    pc = np.asarray(weighted["Pc"], dtype=float)

    nconf = _choose_nconf(l_full, float(cfg["CI"]))
    z_reduced = z_full[:, :nconf]
    eigvals_reduced = l_full[:nconf]

    alpha_train = pc.T @ w @ z_reduced

    return PmeModel(
        mode=mode,
        cfg=cfg,
        layout=layout,
        p0=p0,
        delta_m=delta_m,
        pc=pc,
        w=w,
        z_reduced=z_reduced,
        eigvals_reduced=eigvals_reduced,
        eigvals_full=l_full,
        z_full=z_full,
        alpha_train=np.asarray(alpha_train, dtype=float),
        uinfo=uinfo,
        nconf=nconf,
        baseline_col=baseline_col,
        db_used_shape=(p.shape[0], p.shape[1]),
        filter_mask=np.asarray(filter_mask, dtype=bool),
        filter_info=filter_info,
        stats_w=weighted["statsW"],  # type: ignore[arg-type]
    )


def fit_from_case(case_json: str | Path) -> PmeModel:
    cfg, _ = load_case_json(case_json)

    io_cfg = dict(cfg.get("io", {}) or {})
    vars_cfg = dict(cfg.get("vars", {}) or {})

    dbfile = io_cfg.get("dbfile")
    if not dbfile:
        raise ValueError("cfg.io.dbfile is required")

    db = load_mat_database(dbfile)

    urange_file = vars_cfg.get("Urange_file")
    urange = load_mat_range(urange_file) if urange_file else None

    return fit_pme(db, cfg, urange_full=urange)
