from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray


Array = NDArray[np.float64]


def _safe_invv(x: float) -> float:
    return 1.0 / max(float(x), np.finfo(float).eps)


def _sum_row_variances(block: Array) -> float:
    if block.size == 0:
        return 0.0
    return float(np.sum(np.var(block, axis=1, ddof=0)))


def _pack_stats(
    mode: str,
    dlen: int,
    ulen: int,
    flen: int,
    clen: int,
    n_dinfo: int,
    n_finfo: int,
    n_cinfo: int,
) -> dict[str, Any]:
    return {
        "mode": mode,
        "sizes": {"D": dlen, "U": ulen, "F": flen, "C": clen},
        "ninfo": {
            "D": n_dinfo,
            "F": n_finfo,
            "C": n_cinfo,
            "total": n_dinfo + n_finfo + n_cinfo,
        },
    }


def build_wf(
    delta: Array,
    ptr_in: int,
    layout: dict[str, Any],
    flen: int,
) -> tuple[Array, int, int]:
    """
    Build weights for F block: 1 information per field condition.

    Python port of MATLAB build_WF(delta, ptr_in, offset, layout, Flen).

    Parameters
    ----------
    delta
        Delta matrix in P-space, shape [Np x S]
    ptr_in
        0-based starting row in delta for the F block
    layout
        Parsed layout dictionary
    flen
        Number of F rows in P

    Returns
    -------
    wf
        [flen x flen] diagonal block
    n_finfo
        Number of field information sources
    ptr_out
        Updated 0-based row pointer in delta
    """
    if flen <= 0:
        return np.zeros((0, 0), dtype=float), 0, ptr_in

    wf = np.zeros((flen, flen), dtype=float)
    n_finfo = 0
    ptr = int(ptr_in)

    f_layout = dict(layout.get("F", {}) or {})
    items = list(f_layout.get("items", []) or [])

    if items:
        local = 0
        for item in items:
            n_cond = int(item["nCond"])
            n_rows = int(item["nRows"])
            k = int(n_rows // max(n_cond, 1))

            for _ in range(n_cond):
                rr_delta = slice(ptr, ptr + k)
                var_block = _sum_row_variances(delta[rr_delta, :])
                w = _safe_invv(var_block)

                rr_w = slice(local, local + k)
                wf[rr_w, rr_w] = w * np.eye(k, dtype=float)

                ptr += k
                local += k
                n_finfo += 1
    else:
        # fallback: treat whole F block as 1 information source
        rr_delta = slice(ptr, ptr + flen)
        var_f = _sum_row_variances(delta[rr_delta, :])
        w_f = _safe_invv(var_f)
        wf[:, :] = w_f * np.eye(flen, dtype=float)
        ptr += flen
        n_finfo = 1

    return wf, n_finfo, ptr


def build_wc(
    delta: Array,
    ptr_in: int,
    layout: dict[str, Any],
    clen: int,
) -> tuple[Array, int]:
    """
    Build weights for C block: 1 information per scalar condition.

    Python port of MATLAB build_WC(delta, ptr_in, offset, layout, Clen).

    Parameters
    ----------
    delta
        Delta matrix in P-space, shape [Np x S]
    ptr_in
        0-based starting row in delta for the C block
    layout
        Parsed layout dictionary
    clen
        Number of C rows in P

    Returns
    -------
    wc
        [clen x clen] diagonal block
    n_cinfo
        Number of scalar information sources
    """
    if clen <= 0:
        return np.zeros((0, 0), dtype=float), 0

    wc = np.zeros((clen, clen), dtype=float)
    n_cinfo = 0

    c_layout = dict(layout.get("C", {}) or {})
    items = list(c_layout.get("items", []) or [])

    if items:
        ptr = int(ptr_in)
        local = 0
        for item in items:
            n_cond = int(item["nCond"])
            for _ in range(n_cond):
                rr_delta = ptr
                v = float(np.var(delta[rr_delta, :], ddof=0))
                w = _safe_invv(v)

                wc[local, local] = w

                ptr += 1
                local += 1
                n_cinfo += 1
    else:
        # fallback: treat whole C block as 1 information source
        rr_delta = slice(ptr_in, ptr_in + clen)
        var_c = _sum_row_variances(delta[rr_delta, :])
        w_c = _safe_invv(var_c)
        wc[:, :] = w_c * np.eye(clen, dtype=float)
        n_cinfo = 1

    return wc, n_cinfo


def build_weights(
    delta: Array,
    layout: dict[str, Any],
    cfg: dict[str, Any],
    uinfo: dict[str, Any],
    blocks: dict[str, Array],
) -> tuple[Array, dict[str, Any]]:
    """
    Build block-diagonal weights W consistent with 'ninf as #information'.

    Faithful Python port of MATLAB +pme/weights.m.

    Idea:
    - each INFORMATION contributes ~1 to trace(W*Cov)
    - geometry D counts as 1 info (when present in P)
    - each field condition counts as 1 info
    - each scalar condition counts as 1 info
    - variables U weight is usually 0

    Parameters
    ----------
    delta
        P - P0, shape [Np x S]
    layout
        Parsed layout
    cfg
        Case configuration
    uinfo
        Variable info dictionary
    blocks
        Dict with raw blocks {"D","Ubase","F","C"} already sliced from DB_used

    Returns
    -------
    W
        Weight matrix [Np x Np]
    stats
        Weight diagnostics consistent with MATLAB
    """
    mode = str(cfg["mode"]).lower()

    dlen = int(layout["D"]["nRows"])
    ulen = int(uinfo["Mact"])
    flen = int(blocks["F"].shape[0]) if "F" in blocks else 0
    clen = int(blocks["C"].shape[0]) if "C" in blocks else 0

    if mode == "pme":
        # P = [D; U]
        n = dlen + ulen
        w = np.zeros((n, n), dtype=float)

        var_d = _sum_row_variances(delta[0:dlen, :])
        w_d = _safe_invv(var_d)
        w[0:dlen, 0:dlen] = w_d * np.eye(dlen, dtype=float)

        # U usually not weighted in PME
        w_u = 0.0
        if w_u > 0.0:
            a = dlen
            b = dlen + ulen
            w[a:b, a:b] = w_u * np.eye(ulen, dtype=float)

        stats = _pack_stats(mode, dlen, ulen, flen, clen, 1, 0, 0)
        stats["wD"] = w_d
        stats["wU"] = w_u
        stats["varD"] = var_d
        stats["varU"] = _sum_row_variances(delta[dlen:dlen + ulen, :])

        return w, stats

    if mode == "pi":
        # P = [D; U; F; C]
        n = dlen + ulen + flen + clen
        w = np.zeros((n, n), dtype=float)

        ptr = 0

        # --- D = 1 information ---
        var_d = _sum_row_variances(delta[ptr:ptr + dlen, :])
        w_d = _safe_invv(var_d)
        w[0:dlen, 0:dlen] = w_d * np.eye(dlen, dtype=float)
        ptr += dlen

        # --- U typically 0 ---
        var_u = _sum_row_variances(delta[ptr:ptr + ulen, :])
        ptr_u0 = ptr
        ptr += ulen

        w_u = 0.0
        if w_u > 0.0:
            a = dlen
            b = dlen + ulen
            w[a:b, a:b] = w_u * np.eye(ulen, dtype=float)

        # --- F: 1 info per field condition ---
        wf, n_finfo, ptr = build_wf(delta, ptr, layout, flen)
        if wf.size > 0:
            a = dlen + ulen
            b = dlen + ulen + flen
            w[a:b, a:b] = wf

        # --- C: 1 info per scalar condition ---
        wc, n_cinfo = build_wc(delta, ptr, layout, clen)
        if wc.size > 0:
            a = dlen + ulen + flen
            b = dlen + ulen + flen + clen
            w[a:b, a:b] = wc

        stats = _pack_stats(mode, dlen, ulen, flen, clen, 1, n_finfo, n_cinfo)
        stats["ptrU0"] = ptr_u0
        stats["wD"] = w_d
        stats["wU"] = w_u
        stats["varD"] = var_d
        stats["varU"] = var_u

        return w, stats

    if mode == "pd":
        # P = [U; F; C]
        n = ulen + flen + clen
        w = np.zeros((n, n), dtype=float)

        # --- U weight 0 ---
        w_u = 0.0
        if w_u > 0.0:
            w[0:ulen, 0:ulen] = w_u * np.eye(ulen, dtype=float)

        var_u = _sum_row_variances(delta[0:ulen, :])

        ptr = ulen

        # --- F: 1 info per field condition ---
        wf, n_finfo, ptr = build_wf(delta, ptr, layout, flen)
        if wf.size > 0:
            a = ulen
            b = ulen + flen
            w[a:b, a:b] = wf

        # --- C: 1 info per scalar condition ---
        wc, n_cinfo = build_wc(delta, ptr, layout, clen)
        if wc.size > 0:
            a = ulen + flen
            b = ulen + flen + clen
            w[a:b, a:b] = wc

        stats = _pack_stats(mode, dlen, ulen, flen, clen, 0, n_finfo, n_cinfo)
        stats["wU"] = w_u
        stats["varU"] = var_u

        if flen == 0:
            stats["warning"] = "PD-PME with no F: physics-driven DR limited by C."

        return w, stats

    raise ValueError(f"Unknown mode: {mode}")
