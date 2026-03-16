from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray


Array = NDArray[np.float64]
BoolArray = NDArray[np.bool_]


@dataclass
class FilterResult:
    db_used: Array
    info: dict[str, Any]
    mask: BoolArray


def _cfg_filters_defaults(cfg: dict[str, Any]) -> dict[str, Any]:
    out = dict(cfg)
    filters = dict(out.get("filters", {}) or {})

    if "remove_nan" not in filters:
        filters["remove_nan"] = True

    goal = dict(filters.get("goal", {}) or {})
    if "enable" not in goal:
        goal["enable"] = False
    filters["goal"] = goal

    iqr = dict(filters.get("iqr", {}) or {})
    if "enable" not in iqr:
        iqr["enable"] = False
    if "k" not in iqr:
        iqr["k"] = 3.0
    if "start_row" not in iqr:
        iqr["start_row"] = "after_geom_vars"
    filters["iqr"] = iqr

    debug = dict(filters.get("debug", {}) or {})
    if "goal_rows" not in debug:
        debug["goal_rows"] = False
    if "iqr_rows" not in debug:
        debug["iqr_rows"] = False
    filters["debug"] = debug

    out["filters"] = filters
    return out


def _baseline_col_zero_based(cfg: dict[str, Any], ns: int) -> int:
    """
    MATLAB uses 1-based baseline_col.
    Python internally uses 0-based indexing.
    """
    bc = int(cfg.get("baseline_col", 1))
    if 1 <= bc <= ns:
        return bc - 1
    if 0 <= bc < ns:
        return bc
    raise ValueError(f"baseline_col={bc} out of bounds for {ns} samples")


def _force_keep_baseline(mask: BoolArray, cfg: dict[str, Any]) -> None:
    ns = mask.size
    bc = _baseline_col_zero_based(cfg, ns)
    mask[bc] = True


def _print_step(tag: str, kept_step: int, in_step: int, kept_cum: int, ns_total: int) -> None:
    print(f"[filters][{tag}] kept {kept_step} / {in_step} (cumulative {kept_cum} / {ns_total})")


def _resolve_goal_row(metric: dict[str, Any], layout: dict[str, Any]) -> int:
    """
    Return 0-based absolute row index in DB.

    JSON convention:
    - metric.row is 0-based absolute DB row
    - metric.c_offset is 0-based offset inside scalar block C

    MATLAB path:
    read_case_json.m converts JSON 0-based -> MATLAB 1-based first,
    then filters.m uses:
        r = layout.C.rows(1) + m.c_offset - 1

    In Python we stay 0-based throughout, so:
        r = layout.C.rows.start + c_offset
    """
    if "row" in metric and metric["row"] not in (None, ""):
        return int(metric["row"])

    if "c_offset" in metric and metric["c_offset"] not in (None, ""):
        c_rows = layout.get("C", {}).get("rows")
        if c_rows is None:
            raise ValueError("[filters][goal] c_offset specified but layout.C.rows is missing")
        return int(c_rows.start) + int(metric["c_offset"])

    raise ValueError("[filters][goal] each metric must define 'row' or 'c_offset'")

def _goal_keep_mask(
    db_current: Array,
    cfg: dict[str, Any],
    layout: dict[str, Any],
) -> BoolArray:
    """
    Goal-oriented hard constraints on currently kept columns.
    Port of the relevant MATLAB logic from filters.m.
    """
    filters_cfg = cfg["filters"]
    goal_cfg = dict(filters_cfg.get("goal", {}) or {})
    debug_cfg = dict(filters_cfg.get("debug", {}) or {})

    metrics = goal_cfg.get("metrics", [])
    if not metrics:
        raise ValueError("[filters][goal] enabled but cfg.filters.goal.metrics is empty")

    keep = np.ones(db_current.shape[1], dtype=bool)

    baseline_col = goal_cfg.get("baseline_col", cfg.get("baseline_col", 1))
    baseline_col = int(baseline_col)
    if 1 <= baseline_col <= db_current.shape[1]:
        bc = baseline_col - 1
    elif 0 <= baseline_col < db_current.shape[1]:
        bc = baseline_col
    else:
        raise ValueError(
            f"[filters][goal] baseline_col={baseline_col} out of bounds "
            f"(1..{db_current.shape[1]})"
        )

    if isinstance(metrics, dict):
        metrics = [metrics]

    for i, metric in enumerate(metrics, start=1):
        m = dict(metric)
        r = _resolve_goal_row(m, layout)

        if r < 0 or r >= db_current.shape[0]:
            raise ValueError(
                f"[filters][goal] metric #{i} resolved row r={r+1} out of bounds "
                f"(1..{db_current.shape[0]})"
            )

        base = float(db_current[r, bc])
        vals = db_current[r, :]

        if bool(debug_cfg.get("goal_rows", False)):
            v2_cur = float(db_current[r, 1]) if db_current.shape[1] >= 2 else np.nan
            print(
                f"[filters][goal][debug] metric {i}: "
                f"rule={str(m.get('rule',''))}, r={r+1}, baseline_col={bc+1}, "
                f"base={base:.6g}, DBcur(r,2)={v2_cur:.6g}"
            )

        rule = str(m.get("rule", "")).lower()

        if rule == "leq_baseline":
            fac = float(m.get("factor", 1.0))
            keep &= vals <= fac * base

        elif rule == "geq_baseline":
            fac = float(m.get("factor", 1.0))
            keep &= vals >= fac * base

        elif rule == "between_baseline":
            if "min" not in m or "max" not in m:
                raise ValueError("[filters][goal] between_baseline requires 'min' and 'max'")
            keep &= (vals >= float(m["min"]) * base) & (vals <= float(m["max"]) * base)

        elif rule == "positive":
            keep &= vals > 0.0

        elif rule == "nonnegative":
            keep &= vals >= 0.0

        else:
            raise ValueError(f"[filters][goal] unknown goal rule: {m.get('rule')}")

    return keep


def _iqr_start_row(layout: dict[str, Any], cfg: dict[str, Any], start_row: Any) -> int:
    """
    Return 0-based starting row for IQR filtering.

    MATLAB default:
      "after_geom_vars" -> first row after D and Ubase in the ORIGINAL DB layout
    """
    if isinstance(start_row, str) and start_row.lower() == "after_geom_vars":
        d_rows = int(layout["D"]["nRows"])
        mbase = int(cfg["vars"]["Mbase"])
        return d_rows + mbase

    r = int(start_row)
    if r >= 1:
        return r - 1
    return r


def _iqr_keep_mask(
    db_current: Array,
    cfg: dict[str, Any],
    layout: dict[str, Any],
) -> BoolArray:
    """
    Legacy row-by-row IQR outlier filter on currently kept columns.

    A column is dropped if, for ANY selected row, its value lies outside:
      [Q1 - k*IQR, Q3 + k*IQR]

    This mirrors the MATLAB intent of a cumulative row-wise physical/outlier filter.
    """
    filters_cfg = cfg["filters"]
    iqr_cfg = dict(filters_cfg.get("iqr", {}) or {})
    debug_cfg = dict(filters_cfg.get("debug", {}) or {})

    k_iqr = float(iqr_cfg.get("k", 3.0))
    start_row = _iqr_start_row(layout, cfg, iqr_cfg.get("start_row", "after_geom_vars"))

    nr = db_current.shape[0]
    if start_row < 0:
        start_row = 0
    if start_row >= nr:
        return np.ones(db_current.shape[1], dtype=bool)

    keep = np.ones(db_current.shape[1], dtype=bool)

    for r in range(start_row, nr):
        vals = db_current[r, :]
        #q1 = float(np.quantile(vals, 0.25))
        #q3 = float(np.quantile(vals, 0.75))
        q1 = float(np.percentile(vals, 25, method="midpoint"))
        q3 = float(np.percentile(vals, 75, method="midpoint"))
        iqr = q3 - q1

        lo = q1 - k_iqr * iqr
        hi = q3 + k_iqr * iqr

        row_keep = (vals >= lo) & (vals <= hi)
        keep &= row_keep

        if bool(debug_cfg.get("iqr_rows", False)):
            dropped = int(np.sum(~row_keep))
            print(
                f"[filters][iqr][debug] row={r+1}, q1={q1:.6g}, q3={q3:.6g}, "
                f"iqr={iqr:.6g}, lo={lo:.6g}, hi={hi:.6g}, dropped={dropped}"
            )

    return keep


def apply_filters(
    db: Array,
    cfg: dict[str, Any],
    layout: dict[str, Any],
) -> FilterResult:
    """
    Apply column-wise filters in the same order as MATLAB:

      1) remove_nan
      2) goal
      3) iqr

    Returns:
      db_used = db[:, mask]
      info    = step-by-step counts
      mask    = boolean mask on ORIGINAL DB columns

    Logging matches MATLAB style.
    """
    db = np.asarray(db, dtype=float)
    ns = db.shape[1]

    cfg = _cfg_filters_defaults(cfg)

    mask = np.ones(ns, dtype=bool)
    info: dict[str, Any] = {"Ns_total": int(ns)}

    # =====================================================
    # (1) NaN filter
    # =====================================================
    if bool(cfg["filters"].get("remove_nan", True)):
        in_step = int(np.sum(mask))
        ok = np.all(np.isfinite(db[:, mask]), axis=0)
        kept_step = int(np.sum(ok))

        idx = np.flatnonzero(mask)
        mask[idx[~ok]] = False

        _force_keep_baseline(mask, cfg)

        info["nan_enable"] = True
        info["nan_in"] = in_step
        info["nan_kept"] = kept_step
        info["nan_dropped"] = in_step - kept_step

        _print_step("nan", kept_step, in_step, int(np.sum(mask)), ns)
    else:
        info["nan_enable"] = False
        info["nan_in"] = int(np.sum(mask))
        info["nan_kept"] = int(np.sum(mask))
        info["nan_dropped"] = 0

        _force_keep_baseline(mask, cfg)
        print(f"[filters][ nan] disabled (cumulative {int(np.sum(mask))} / {ns})")

    # =====================================================
    # (2) Goal filter
    # =====================================================
    goal_cfg = dict(cfg["filters"].get("goal", {}) or {})
    if bool(goal_cfg.get("enable", False)):
        in_step = int(np.sum(mask))

        c_rows = int(layout.get("C", {}).get("nRows", 0))
        if c_rows == 0:
            info["goal_enable"] = True
            info["goal_skipped"] = True
            info["goal_in"] = in_step
            info["goal_kept"] = in_step
            info["goal_dropped"] = 0

            _force_keep_baseline(mask, cfg)
            print(f"[filters][goal] skipped (C empty), cumulative {int(np.sum(mask))} / {ns}")
        else:
            metrics = goal_cfg.get("metrics", [])
            if not metrics:
                info["goal_enable"] = True
                info["goal_skipped"] = True
                info["goal_in"] = in_step
                info["goal_kept"] = in_step
                info["goal_dropped"] = 0

                _force_keep_baseline(mask, cfg)
                print(f"[filters][goal] skipped (metrics empty), cumulative {int(np.sum(mask))} / {ns}")
            else:
                idx_kept = np.flatnonzero(mask)
                db_cur = db[:, idx_kept]

                keep_local = _goal_keep_mask(db_cur, cfg, layout)
                kept_step = int(np.sum(keep_local))

                mask[idx_kept[~keep_local]] = False
                _force_keep_baseline(mask, cfg)

                info["goal_enable"] = True
                info["goal_skipped"] = False
                info["goal_in"] = in_step
                info["goal_kept"] = kept_step
                info["goal_dropped"] = in_step - kept_step

                _print_step("goal", kept_step, in_step, int(np.sum(mask)), ns)
    else:
        info["goal_enable"] = False
        info["goal_skipped"] = False
        info["goal_in"] = int(np.sum(mask))
        info["goal_kept"] = int(np.sum(mask))
        info["goal_dropped"] = 0

        _force_keep_baseline(mask, cfg)
        print(f"[filters][goal] disabled (cumulative {int(np.sum(mask))} / {ns})")

    # =====================================================
    # (3) IQR filter
    # =====================================================
    iqr_cfg = dict(cfg["filters"].get("iqr", {}) or {})
    if bool(iqr_cfg.get("enable", False)):
        in_step = int(np.sum(mask))

        idx_kept = np.flatnonzero(mask)
        db_cur = db[:, idx_kept]

        keep_local = _iqr_keep_mask(db_cur, cfg, layout)
        kept_step = int(np.sum(keep_local))

        mask[idx_kept[~keep_local]] = False
        _force_keep_baseline(mask, cfg)

        info["iqr_enable"] = True
        info["iqr_in"] = in_step
        info["iqr_kept"] = kept_step
        info["iqr_dropped"] = in_step - kept_step

        _print_step(" iqr", kept_step, in_step, int(np.sum(mask)), ns)
    else:
        info["iqr_enable"] = False
        info["iqr_in"] = int(np.sum(mask))
        info["iqr_kept"] = int(np.sum(mask))
        info["iqr_dropped"] = 0

        _force_keep_baseline(mask, cfg)
        print(f"[filters][ iqr] disabled (cumulative {int(np.sum(mask))} / {ns})")

    # =====================================================
    # final
    # =====================================================
    info["total_kept"] = int(np.sum(mask))
    db_used = db[:, mask]

    print(f"[filters] total kept {int(np.sum(mask))} / {ns} samples")

    return FilterResult(
        db_used=np.asarray(db_used, dtype=float),
        info=info,
        mask=np.asarray(mask, dtype=bool),
    )
