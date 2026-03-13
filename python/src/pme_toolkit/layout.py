from __future__ import annotations

from typing import Any


def _field_k(item: dict[str, Any]) -> int:
    disc = item.get("disc", {})
    if not isinstance(disc, dict):
        raise ValueError("Field item.disc must be a dictionary")

    if "K" in disc and disc["K"] is not None:
        return int(disc["K"])

    patches = disc.get("patches", [])
    if patches:
        return int(sum(int(p["K"]) for p in patches))

    raise ValueError("Field discretization must define disc.K or disc.patches")


def parse_layout(cfg: dict[str, Any]) -> dict[str, Any]:
    """Compute row offsets for D, Ubase, F, C based on the case configuration.

    Ordering follows the repository convention:
        DB = [D; Ubase; F; C]
    """
    geom = dict(cfg.get("geom", {}) or {})
    vars_cfg = dict(cfg.get("vars", {}) or {})
    phys = dict(cfg.get("phys", {}) or {})

    jdir = int(geom["Jdir"])
    patches = list(geom.get("patches", []))
    if not patches:
        raise ValueError("cfg.geom.patches is required and cannot be empty")

    ktot = sum(int(p["K"]) for p in patches)
    d_rows = jdir * ktot

    mbase = int(vars_cfg["Mbase"])

    field_items = [dict(x) for x in (phys.get("fields", []) or [])]
    scalar_items = [dict(x) for x in (phys.get("scalars", []) or [])]

    f_rows = 0
    for item in field_items:
        n_cond = int(item.get("nCond", 1))
        k = _field_k(item)
        item["nRows"] = n_cond * k
        f_rows += item["nRows"]

    c_rows = 0
    for item in scalar_items:
        n_cond = int(item.get("nCond", 1))
        item["nRows"] = n_cond
        c_rows += n_cond

    r0 = 0
    d_slice = slice(r0, r0 + d_rows)
    r0 += d_rows

    u_slice = slice(r0, r0 + mbase)
    r0 += mbase

    f_slice = slice(r0, r0 + f_rows)
    r0 += f_rows

    c_slice = slice(r0, r0 + c_rows)
    r0 += c_rows

    return {
        "geom": geom,
        "vars": vars_cfg,
        "phys": phys,
        "D": {"nRows": d_rows, "rows": d_slice},
        "Ubase": {"nRows": mbase, "rows": u_slice},
        "F": {"nRows": f_rows, "rows": f_slice, "items": field_items},
        "C": {"nRows": c_rows, "rows": c_slice, "items": scalar_items},
        "totalRows": r0,
    }
