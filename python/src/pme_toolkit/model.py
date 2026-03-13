from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.linalg import eig

from .config_loader import load_case_json
from .filters import apply_filters
from .io import load_mat_database, load_mat_range
from .layout import parse_layout
from .weights import build_weights


Array = NDArray[np.float64]


def _defaults(cfg: dict[str, Any]) -> dict[str, Any]:
    out = dict(cfg)

    out.setdefault("mode", "pme")
    out.setdefault("CI", 0.95)
    out.setdefault("baseline_col", 1)  # MATLAB-style default (1-based)

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
    eigvals = np.asarray(eigvals, dtype=float).reshape(-1)
    if eigvals.size == 0:
        return 1

    cum = np.cumsum(eigvals)
    tot = float(cum[-1])
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
        if int(layout["F"]["nRows"]) > 0
        else np.zeros((0, db.shape[1]), dtype=float),
        "C": np.asarray(db[c_slice, :], dtype=float)
        if int(layout["C"]["nRows"]) > 0
        else np.zeros((0, db.shape[1]), dtype=float),
    }


def _convert_idx_active(
    idx_active: list[int] | tuple[int, ...] | Array | None,
    mbase: int,
) -> Array:
    if idx_active is None or len(idx_active) == 0:
        return np.arange(mbase, dtype=int)

    idx = np.asarray(idx_active, dtype=int).ravel()

    # Repository JSON is usually 0-based. But allow 1-based manual input.
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

    src_label = "user" if urange_source == "user" else urange_source
    print(
        f"[vars] normalized Uact using {src_label} Urange; "
        f"min/max after clip = {float(np.min(uact)):.3e} / {float(np.max(uact)):.6g} "
        f"(Mact={int(idx_active.size)})"
    )

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
        # P = [D; U]
        return np.vstack([d, uact])

    if mode == "pi":
        # P = [D; U; F; C]
        blocks = [d, uact]
        if f.size > 0:
            blocks.append(f)
        if c.size > 0:
            blocks.append(c)
        return np.vstack(blocks)

    if mode == "pd":
        # P = [U; F; C]
        blocks = [uact]
        if f.size > 0:
            blocks.append(f)
        if c.size > 0:
            blocks.append(c)
        return np.vstack(blocks)

    raise ValueError(f"Unknown mode: {mode}")


def _baseline_col_zero_based(cfg: dict[str, Any], ns: int) -> int:
    """
    MATLAB-style baseline_col is 1-based.
    Allow also Python-style 0-based for robustness.
    """
    bc = int(cfg.get("baseline_col", 1))
    if 1 <= bc <= ns:
        return bc - 1
    if 0 <= bc < ns:
        return bc
    raise ValueError(f"baseline_col={bc} out of range for {ns} samples")


def _baseline_col_local(cfg: dict[str, Any], filter_mask: Array, ns_local: int) -> int:
    """
    Convert baseline_col from original DB indexing to local filtered DB indexing.

    Since filters always force baseline to survive, this should always succeed.
    """
    mask = np.asarray(filter_mask, dtype=bool).reshape(-1)
    ns_total = mask.size
    bc_orig = _baseline_col_zero_based(cfg, ns_total)

    kept = np.flatnonzero(mask)
    loc = np.where(kept == bc_orig)[0]
    if loc.size == 0:
        raise ValueError("baseline column was not found among kept columns")
    bc_local = int(loc[0])

    if bc_local < 0 or bc_local >= ns_local:
        raise ValueError(f"Local baseline_col={bc_local} out of range for {ns_local} samples")

    return bc_local


def _u_rows_in_p(mode: str, dlen: int, mact: int) -> tuple[int, int]:
    mode = mode.lower()

    if mode in ("pme", "pi"):
        start = dlen
        stop = dlen + mact
        return start, stop

    if mode == "pd":
        start = 0
        stop = mact
        return start, stop

    raise ValueError(f"Unknown mode: {mode}")


def _weighted_fit(
    p: Array,
    mode: str,
    layout: dict[str, Any],
    uinfo: dict[str, Any],
    blocks: dict[str, Array],
    cfg: dict[str, Any],
    baseline_col: int,
) -> dict[str, Array | dict[str, Any]]:
    """
    Generic weighted fit for PME / PI-PME / PD-PME.
    """
    s = p.shape[1]

    p0 = p[:, [baseline_col]]
    delta = p - p0
    delta_m = np.mean(delta, axis=1, keepdims=True)
    pc = delta - delta_m

    w, stats_w = build_weights(delta, layout, cfg, uinfo, blocks)

    a = (pc @ pc.T) / float(s)
    aw = a @ w

    eigvals_raw, eigvecs_raw = eig(aw)
    eigvals_raw = np.real(eigvals_raw)
    eigvecs_raw = np.real(eigvecs_raw)

    order = np.argsort(eigvals_raw)[::-1]
    l_full = np.maximum(eigvals_raw[order], 0.0)
    z_full = eigvecs_raw[:, order]

    # Normalize Z so that Z' W Z = I
    an = np.diag(z_full.T @ w @ z_full)
    an = np.sqrt(np.maximum(an, np.finfo(float).eps))
    z_full = z_full / an[None, :]

    ak_full = pc.T @ w @ z_full

    return {
        "P0": p0,
        "delta_m": delta_m,
        "W": w,
        "statsW": stats_w,
        "L_full": l_full,
        "Z_full": z_full,
        "Pc": pc,
        "ak_full": ak_full,
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
    ak_full: Array
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

    def transform_valid(self, db: Array) -> Array:
        """
        Transform only the columns retained by the fit-time filter mask.
        Useful when db is the original full database.
        """
        db = np.asarray(db, dtype=float)
        mask = np.asarray(self.filter_mask, dtype=bool)
        if db.shape[1] != mask.size:
            raise ValueError(
                f"DB has {db.shape[1]} samples but filter_mask has length {mask.size}"
            )
        return self.transform(db[:, mask])

    def inverse_active(self, alpha: Array) -> Array:
        alpha = np.asarray(alpha, dtype=float)
        alpha = np.atleast_2d(alpha)
        if alpha.shape[1] != self.nconf:
            raise ValueError(f"alpha must have {self.nconf} columns")

        p_hat = self.p0[:, [0]] + self.delta_m[:, [0]] + self.z_reduced @ alpha.T

        d_rows = int(self.layout["D"]["nRows"])
        u_rows = int(self.uinfo["Mact"])
        start, stop = _u_rows_in_p(self.mode, d_rows, u_rows)

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


def fit_model(
    db: Array,
    cfg: dict[str, Any],
    *,
    urange_full: Array | None = None,
    filter_mask: Array | None = None,
    filter_info: dict[str, Any] | None = None,
    db_total_shape: tuple[int, int] | None = None,
) -> PmeModel:
    """
    Generic fit for PME / PI-PME / PD-PME.

    Behavior:
    - if filter_mask/filter_info are provided, assume db is already DB_used
    - otherwise apply filters internally as a fallback, so standalone use still works
    """
    cfg = _defaults(cfg)
    mode = str(cfg["mode"]).lower()

    if mode not in ("pme", "pi", "pd"):
        raise ValueError(f"Unsupported mode: {mode}")

    layout = parse_layout(cfg)
    db = np.asarray(db, dtype=float)

    # Fallback behavior for standalone calls
    if filter_mask is None or filter_info is None:
        filt = apply_filters(db, cfg, layout)
        db_fit = np.asarray(filt.db_used, dtype=float)
        filter_mask = np.asarray(filt.mask, dtype=bool)
        filter_info = dict(filt.info)
        if db_total_shape is None:
            db_total_shape = tuple(db.shape)
    else:
        db_fit = np.asarray(db, dtype=float)
        filter_mask = np.asarray(filter_mask, dtype=bool)
        filter_info = dict(filter_info)
        if db_total_shape is None:
            db_total_shape = tuple(db.shape)

    blocks = _slice_blocks(db_fit, layout)
    uact, uinfo = _prepare_vars(blocks["Ubase"], cfg, urange_full)
    p = _compose_p(mode, blocks["D"], uact, blocks["F"], blocks["C"])

    baseline_col = _baseline_col_local(cfg, filter_mask, p.shape[1])

    weighted = _weighted_fit(
        p,
        mode,
        layout,
        uinfo,
        blocks,
        cfg,
        baseline_col,
    )

    l_full = np.asarray(weighted["L_full"], dtype=float)
    z_full = np.asarray(weighted["Z_full"], dtype=float)
    w = np.asarray(weighted["W"], dtype=float)
    p0 = np.asarray(weighted["P0"], dtype=float)
    delta_m = np.asarray(weighted["delta_m"], dtype=float)
    pc = np.asarray(weighted["Pc"], dtype=float)
    ak_full = np.asarray(weighted["ak_full"], dtype=float)

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
        ak_full=ak_full,
        uinfo=uinfo,
        nconf=nconf,
        baseline_col=baseline_col,
        db_used_shape=(p.shape[0], p.shape[1]),
        filter_mask=np.asarray(filter_mask, dtype=bool),
        filter_info=dict(filter_info),
        stats_w=weighted["statsW"],  # type: ignore[arg-type]
    )


def fit_pme(
    db: Array,
    cfg: dict[str, Any],
    *,
    urange_full: Array | None = None,
    filter_mask: Array | None = None,
    filter_info: dict[str, Any] | None = None,
    db_total_shape: tuple[int, int] | None = None,
) -> PmeModel:
    """
    Backward-compatible public entry point.

    Despite the historical name, this now supports:
      - mode='pme'
      - mode='pi'
      - mode='pd'
    based on cfg["mode"].
    """
    return fit_model(
        db,
        cfg,
        urange_full=urange_full,
        filter_mask=filter_mask,
        filter_info=filter_info,
        db_total_shape=db_total_shape,
    )


def fit_from_case(case_json: str | Path) -> PmeModel:
    """
    Load case.json + .mat inputs and fit the model.

    Standalone path: filters are applied internally by fit_pme(...)
    if not handled upstream by run_case.py.
    """
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
