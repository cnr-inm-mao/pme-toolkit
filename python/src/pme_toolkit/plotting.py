from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import matplotlib.pyplot as plt

from .model import PmeModel

plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "axes.grid": False,
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "legend.fontsize": 9,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
    }
)

# ============================================================================
# Helpers
# ============================================================================

def _ensure_outdir(outdir: str | Path | None) -> Path:
    if outdir is None:
        outdir = Path.cwd() / "results"
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    return out


def _as_1d(x: Any) -> np.ndarray:
    return np.asarray(x, dtype=float).reshape(-1)


def _mact(model: PmeModel) -> int:
    uinfo = getattr(model, "uinfo", None)
    if isinstance(uinfo, dict) and "Mact" in uinfo:
        return int(uinfo["Mact"])
    return int(model.cfg["vars"]["Mbase"])


def _mode_str(model: PmeModel) -> str:
    return str(model.mode).lower()


def _ninf(model: PmeModel) -> int:
    layout = model.layout
    mode = _mode_str(model)

    nphys = 0

    f = layout.get("F", {})
    if isinstance(f, dict) and f.get("items"):
        for item in f["items"]:
            nphys += int(item.get("nCond", 1))
    elif isinstance(f, dict) and int(f.get("nRows", 0)) > 0:
        nphys += 1

    c = layout.get("C", {})
    if isinstance(c, dict) and c.get("items"):
        for item in c["items"]:
            nphys += int(item.get("nCond", 1))
    elif isinstance(c, dict) and int(c.get("nRows", 0)) > 0:
        nphys += 1

    if mode == "pme":
        return 1
    if mode == "pi":
        return 1 + nphys
    if mode == "pd":
        return nphys

    raise ValueError(f"Unknown mode: {mode}")


def _kplot(model: PmeModel) -> int:
    mact = _mact(model)
    lam = _as_1d(model.eigvals_full)
    return int(min(mact, lam.size))


def _p_blocks(model: PmeModel) -> dict[str, np.ndarray]:
    """Python port of local_p_blocks used in MATLAB plotting code."""
    cfg = model.cfg
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


@dataclass
class _Source:
    name: str
    type: str
    group: str
    cond: int
    nCond: int
    rows: np.ndarray


def _field_k(item: dict[str, Any]) -> int:
    disc = item.get("disc", {})
    if isinstance(disc, dict) and disc.get("K") is not None:
        return int(disc["K"])

    patches = disc.get("patches", []) if isinstance(disc, dict) else []
    if patches:
        return int(sum(int(p["K"]) for p in patches))

    raise ValueError("Field discretization must define disc.K or disc.patches")


def _build_info_sources(model: PmeModel) -> list[_Source]:
    """Python port of pme_build_info_sources for plotting/reporting."""
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

    # fields
    if pos["F"].size > 0:
        offset = 0
        items = list(layout.get("F", {}).get("items", []) or [])
        for item in items:
            name = str(item.get("name", "field"))
            n_cond = int(item.get("nCond", 1))
            k = _field_k(item)
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
            offset += n_cond * k

    # scalars
    if pos["C"].size > 0:
        offset = 0
        items = list(layout.get("C", {}).get("items", []) or [])
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

    return sources


def _local_shade(base: np.ndarray, cond: int, ncond: int) -> np.ndarray:
    if ncond <= 1:
        return base.copy()

    t = 0.00 + 0.35 * (cond - 1) / max(ncond - 1, 1)
    c = (1 - t) * base + t * np.array([1.0, 1.0, 1.0])
    return np.clip(c, 0.0, 0.95)


def source_colors(sources: list[_Source]) -> np.ndarray:
    """Python port of source_colors.m."""
    n = len(sources)
    colors = np.zeros((n, 3), dtype=float)
    if n == 0:
        return colors

    geom_color = np.array([0.20, 0.20, 0.20], dtype=float)

    field_bases = np.array(
        [
            [0.00, 0.45, 0.70],
            [0.00, 0.62, 0.45],
            [0.35, 0.55, 0.85],
            [0.50, 0.40, 0.75],
        ],
        dtype=float,
    )

    scalar_bases = np.array(
        [
            [0.90, 0.60, 0.00],
            [0.80, 0.40, 0.00],
            [0.80, 0.47, 0.65],
            [0.65, 0.37, 0.15],
        ],
        dtype=float,
    )

    field_groups: list[str] = []
    scalar_groups: list[str] = []

    for i, src in enumerate(sources):
        typ = str(src.type).lower()
        grp = str(src.group)
        cond = int(src.cond)
        ncond = int(src.nCond)

        if typ == "geom":
            colors[i, :] = geom_color
        elif typ == "field":
            if grp not in field_groups:
                field_groups.append(grp)
            idx = field_groups.index(grp)
            base = field_bases[idx % field_bases.shape[0], :]
            colors[i, :] = _local_shade(base, cond, ncond)
        elif typ == "scalar":
            if grp not in scalar_groups:
                scalar_groups.append(grp)
            idx = scalar_groups.index(grp)
            base = scalar_bases[idx % scalar_bases.shape[0], :]
            colors[i, :] = _local_shade(base, cond, ncond)
        else:
            colors[i, :] = np.array([0.0, 0.0, 0.0], dtype=float)

    return colors


def _mode_scale(model: PmeModel, j: int) -> float:
    """Python port of local_mode_sigma_scale."""
    if j < len(model.eigvals_reduced):
        lam = float(np.real(model.eigvals_reduced[j]))
    elif j < len(model.eigvals_full):
        lam = float(np.real(model.eigvals_full[j]))
    else:
        raise ValueError("No eigenvalue available to scale geometric mode.")
    lam = max(lam, 0.0)
    return 3.0 * np.sqrt(lam)


def _reconstruction_curves(model: PmeModel) -> dict[str, Any]:
    """Compute the same source-wise curves used by MATLAB report + plots."""
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
    w = np.asarray(model.w, dtype=float)

    var_src = np.zeros((ninf,), dtype=float)
    for i, src in enumerate(sources):
        rr = src.rows
        var_src[i] = float(np.sum(np.var(pc[rr, :], axis=1, ddof=0)))

    nmse_t = np.zeros((ninf, kplot), dtype=float)

    for jconf in range(1, kplot + 1):
        k = jconf
        zk = z_full[:, :k]
        ak = pc.T @ w @ zk
        prec = zk @ ak.T
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

    lam = _as_1d(model.eigvals_full)
    lam_cum = np.cumsum(lam[:kplot]) / max(float(ninf), np.finfo(float).eps)

    return {
        "enable": True,
        "k_grid": np.arange(1, kplot + 1, dtype=int),
        "sources": sources,
        "var_src": var_src,
        "nmse_t": np.real(nmse_t),
        "var_t": np.real(var_t),
        "var_p": np.real(var_p),
        "nmse_global": np.real(nmse_global),
        "ev_global": np.real(ev_global),
        "lam_cum_ninf": np.real(lam_cum),
    }


# ============================================================================
# Plot ports from MATLAB
# ============================================================================

def plot_scree_plot(model: PmeModel, outdir: str | Path | None = None) -> None:
    """Improved Python port of plot_scree_plot.m."""
    out = _ensure_outdir(outdir)

    lam = _as_1d(model.eigvals_full)
    nconf = int(model.nconf)

    if lam.size == 0:
        return

    mplot = min(_mact(model), lam.size)
    x = np.arange(1, mplot + 1, dtype=int)
    y = lam[:mplot]

    fig, ax = plt.subplots(figsize=(7.2, 5.0), facecolor="white")

    (h1,) = ax.plot(
        x,
        y,
        "o-",
        linewidth=1.2,
        markersize=4.5,
        markerfacecolor="white",
    )

    ymin = float(np.min(y))
    ymax = float(np.max(y))
    if ymax <= ymin:
        ymax = ymin + 1.0

    xline = min(nconf, mplot)
    (h2,) = ax.plot(
        [xline, xline],
        [ymin, ymax],
        ":",
        linewidth=1.2,
    )

    ax.grid(True, alpha=0.30)
    ax.set_xlabel("Mode index [-]")
    ax.set_ylabel(r"Eigenvalue $\lambda_j$ [-]")
    ax.set_title(f"Eigenvalue spectrum ({str(model.mode).upper()})", fontweight="bold")
    ax.set_xlim(1, mplot)

    yr = ymax - ymin
    ax.set_ylim(max(0.0, ymin - 0.05 * yr), ymax + 0.05 * yr)

    ax.legend(
        [h1, h2],
        [r"$\lambda_j$", "selected N"],
        loc="upper right",
        frameon=True,
    )

    fig.tight_layout()
    fig.savefig(out / "scree_plot.png", bbox_inches="tight", dpi=220)
    plt.close(fig)

def plot_variance_retained(model: PmeModel, outdir: str | Path | None = None) -> None:
    """Improved Python port of plot_variance_retained.m."""
    out = _ensure_outdir(outdir)

    lam = _as_1d(model.eigvals_full)
    nconf = int(model.nconf)
    kmax = min(_mact(model), lam.size)
    ninf = _ninf(model)

    if kmax < 1:
        return

    x = np.arange(1, kmax + 1, dtype=int)
    cum_pct = 100.0 * np.cumsum(lam[:kmax]) / max(float(ninf), np.finfo(float).eps)

    fig, ax = plt.subplots(figsize=(7.2, 5.0), facecolor="white")

    h0 = ax.axhspan(95.0, 100.0, alpha=0.18)
    (h1,) = ax.plot(
        x,
        cum_pct,
        "o-",
        linewidth=1.2,
        markersize=4.5,
        markerfacecolor="white",
    )
    (h2,) = ax.plot(
        [1, kmax],
        [99.0, 99.0],
        "--",
        linewidth=1.0,
    )

    xline = min(nconf, kmax)
    (h3,) = ax.plot(
        [xline, xline],
        [0.0, 100.0],
        ":",
        linewidth=1.2,
    )

    ax.grid(True, alpha=0.30)
    ax.set_xlabel("Number of retained modes, k [-]")
    ax.set_ylabel("Retained variance [%]")
    ax.set_title(f"Retained variance ({str(model.mode).upper()})", fontweight="bold")
    ax.set_xlim(1, kmax)
    ax.set_ylim(0, 100)

    ax.legend(
        [h0, h1, h2, h3],
        ["95% threshold", "cumulative", "99% threshold", "selected N"],
        loc="lower right",
        frameon=True,
    )

    fig.tight_layout()
    fig.savefig(out / "variance_retained.png", bbox_inches="tight", dpi=220)
    plt.close(fig)

def plot_nmse_by_source(model: PmeModel, outdir: str | Path | None = None) -> None:
    """Improved Python port of plot_nmse_by_source.m."""
    out = _ensure_outdir(outdir)
    rep = _reconstruction_curves(model)

    if not rep["enable"]:
        return

    k = np.asarray(rep["k_grid"], dtype=int)
    nmse_t = np.asarray(rep["nmse_t"], dtype=float)
    sources: list[_Source] = rep["sources"]
    colors = source_colors(sources)

    fig, ax = plt.subplots(figsize=(7.2, 5.0), facecolor="white")

    handles = []
    labels = []

    for i in range(nmse_t.shape[0]):
        (h,) = ax.plot(
            k,
            nmse_t[i, :],
            "o-",
            linewidth=1.1,
            markersize=4.2,
            markerfacecolor="white",
            color=colors[i, :],
        )
        handles.append(h)
        labels.append(str(sources[i].name))

    xline = min(int(model.nconf), int(k[-1]))
    ax.plot([xline, xline], [0.0, max(1e-12, float(np.nanmax(nmse_t)))], ":", linewidth=1.0)

    ax.grid(True, alpha=0.30)
    ax.set_xlabel("Number of retained modes, k [-]")
    ax.set_ylabel("NMSE [-]")
    ax.set_title(f"NMSE by information source ({str(model.mode).upper()})", fontweight="bold")
    ax.set_xlim(int(k[0]), int(k[-1]))

    ymax = float(np.nanmax(nmse_t))
    if not np.isfinite(ymax) or ymax <= 0.0:
        ymax = 1.0
    ax.set_ylim(0.0, 1.05 * ymax)

    ax.legend(handles, labels, loc="upper right", frameon=True)

    fig.tight_layout()
    fig.savefig(out / "nmse_by_source.png", bbox_inches="tight", dpi=220)
    plt.close(fig)

def plot_variance_by_source(model: PmeModel, outdir: str | Path | None = None) -> None:
    """Improved Python port of plot_variance_by_source.m."""
    out = _ensure_outdir(outdir)
    rep = _reconstruction_curves(model)

    if not rep["enable"]:
        return

    k = np.asarray(rep["k_grid"], dtype=int)
    var_t = np.asarray(rep["var_t"], dtype=float)
    sources: list[_Source] = rep["sources"]
    colors = source_colors(sources)

    fig, ax = plt.subplots(figsize=(7.2, 5.0), facecolor="white")

    handles = []
    labels = []

    for i in range(var_t.shape[0]):
        (h,) = ax.plot(
            k,
            var_t[i, :],
            "o-",
            linewidth=1.1,
            markersize=4.2,
            markerfacecolor="white",
            color=colors[i, :],
        )
        handles.append(h)
        labels.append(str(sources[i].name))

    xline = min(int(model.nconf), int(k[-1]))
    ax.plot([xline, xline], [0.0, 1.0], ":", linewidth=1.0)

    ax.grid(True, alpha=0.30)
    ax.set_xlabel("Number of retained modes, k [-]")
    ax.set_ylabel("Retained variance [-]")
    ax.set_title(
        f"Retained variance by information source ({str(model.mode).upper()})",
        fontweight="bold",
    )
    ax.set_xlim(int(k[0]), int(k[-1]))
    ax.set_ylim(0.0, 1.05)

    ax.legend(handles, labels, loc="lower right", frameon=True)

    fig.tight_layout()
    fig.savefig(out / "variance_by_source.png", bbox_inches="tight", dpi=220)
    plt.close(fig)

def plot_variable_modes(model: PmeModel, outdir: str | Path | None = None) -> None:
    """Single-column variable mode plot, closer to MATLAB layout."""
    out = _ensure_outdir(outdir)

    pos = _p_blocks(model)
    if pos["U"].size == 0:
        return

    z = np.asarray(model.z_reduced, dtype=float)
    nconf = z.shape[1]
    mact = _mact(model)
    u_modes = z[pos["U"], :nconf]

    if nconf < 1:
        return

    x = np.arange(1, mact + 1, dtype=int)

    # one column, but wide and with squat subplots
    fig, axes = plt.subplots(
        nconf,
        1,
        figsize=(9.5, max(1.15 * nconf, 6.5)),
        facecolor="white",
        squeeze=False,
        sharex=True,
    )
    axes = axes.ravel()

    for j in range(nconf):
        ax = axes[j]

        uj = np.abs(u_modes[:, j])
        den = float(np.max(uj))
        if den < np.finfo(float).eps:
            uj = np.zeros_like(uj)
        else:
            uj = uj / den

        ax.plot(
            x,
            uj,
            "o-",
            linewidth=0.9,
            markersize=4.0,
            markerfacecolor="white",
        )

        ax.set_xlim(1, mact)
        ax.set_ylim(0.0, 1.05)
        ax.grid(True, alpha=0.30)
        ax.set_ylabel(rf"$m_{{{j+1}}}$", rotation=0, labelpad=18, fontsize=10)

        if j < nconf - 1:
            ax.tick_params(labelbottom=False)
        else:
            ax.set_xlabel("Eigenvector variable components [-]")

    fig.suptitle(
        f"Normalized absolute variable participation per retained mode ({str(model.mode).upper()})",
        fontweight="bold",
        fontsize=13,
    )
    fig.tight_layout(rect=[0.04, 0.03, 1.00, 0.96])

    fig.savefig(out / "variable_modes_normalized.png", bbox_inches="tight", dpi=220)
    plt.close(fig)

def plot_modes(model: PmeModel, outdir: str | Path | None = None, n_modes: int = 3) -> None:
    """Geometric mode plots with MATLAB-like reshape and scatter rendering."""
    out = _ensure_outdir(outdir)

    mode = _mode_str(model)
    if mode == "pd":
        return

    cfg = model.cfg
    geom = cfg.get("geom", {})
    if "Jdir" not in geom or "patches" not in geom:
        return

    jdir = int(geom["Jdir"])
    patches = list(geom["patches"])
    kpatch = [int(p["K"]) for p in patches]
    ktot = int(sum(kpatch))
    drows = jdir * ktot

    p0 = _as_1d(model.p0)
    if p0.size < drows:
        return

    zr = np.asarray(model.z_reduced, dtype=float)
    if zr.size == 0:
        return

    n_modes = int(min(n_modes, zr.shape[1]))
    if n_modes < 1:
        return

    d0 = p0[:drows]
    scales = np.zeros((n_modes,), dtype=float)

    def _matlab_reshape_geom(vec: np.ndarray, k: int, jdir: int) -> np.ndarray:
        """Replicate MATLAB reshape(vec, [k, jdir]) behavior."""
        return np.asarray(vec, dtype=float).reshape((k, jdir), order="F")

    if jdir == 2:
        xmin, xmax = np.inf, -np.inf
        ymin, ymax = np.inf, -np.inf
    elif jdir == 3:
        xmin, xmax = np.inf, -np.inf
        ymin, ymax = np.inf, -np.inf
        zmin, zmax = np.inf, -np.inf
    else:
        return

    # global limits across all plotted modes
    for j in range(n_modes):
        phi = zr[:drows, j]
        scales[j] = _mode_scale(model, j)

        offset = 0
        for k in kpatch:
            rows = slice(offset, offset + jdir * k)

            g0 = _matlab_reshape_geom(d0[rows], k, jdir)
            gp = _matlab_reshape_geom(d0[rows] + scales[j] * phi[rows], k, jdir)
            gm = _matlab_reshape_geom(d0[rows] - scales[j] * phi[rows], k, jdir)

            gall = np.vstack([g0, gp, gm])

            xmin = min(xmin, float(np.min(gall[:, 0])))
            xmax = max(xmax, float(np.max(gall[:, 0])))
            ymin = min(ymin, float(np.min(gall[:, 1])))
            ymax = max(ymax, float(np.max(gall[:, 1])))

            if jdir == 3:
                zmin = min(zmin, float(np.min(gall[:, 2])))
                zmax = max(zmax, float(np.max(gall[:, 2])))

            offset += jdir * k

    xspan = max(xmax - xmin, np.finfo(float).eps)
    yspan = max(ymax - ymin, np.finfo(float).eps)
    xpad = 0.03 * xspan
    ypad = 0.03 * yspan
    xmin -= xpad
    xmax += xpad
    ymin -= ypad
    ymax += ypad

    if jdir == 3:
        zspan = max(zmax - zmin, np.finfo(float).eps)
        zpad = 0.03 * zspan
        zmin -= zpad
        zmax += zpad
        xspan = xmax - xmin
        yspan = ymax - ymin
        zspan = zmax - zmin

    # draw each retained mode
    for j in range(n_modes):
        phi = zr[:drows, j]
        scale = scales[j]

        if jdir == 3:
            fig = plt.figure(figsize=(8.4, 5.8), facecolor="white")
            ax = fig.add_subplot(111, projection="3d")
        else:
            fig, ax = plt.subplots(figsize=(7.4, 5.2), facecolor="white")

        offset = 0
        first_patch = True
        for k in kpatch:
            rows = slice(offset, offset + jdir * k)

            g0 = _matlab_reshape_geom(d0[rows], k, jdir)
            gp = _matlab_reshape_geom(d0[rows] + scale * phi[rows], k, jdir)
            gm = _matlab_reshape_geom(d0[rows] - scale * phi[rows], k, jdir)

            if jdir == 3:
                ax.scatter(
                        g0[:, 0], g0[:, 1], g0[:, 2],
                        s=12,
                        facecolors="none",
                        edgecolors="k",
                        linewidths=0.8,
                        marker="o",
                        label="baseline" if first_patch else None,
                        depthshade=False,
                        )
                ax.scatter(
                        gp[:, 0], gp[:, 1], gp[:, 2],
                        s=10,
                        facecolors="none",
                        edgecolors="b",
                        linewidths=0.7,
                        marker="o",
                        label="+ mode" if first_patch else None,
                        depthshade=False,
                        )
                ax.scatter(
                        gm[:, 0], gm[:, 1], gm[:, 2],
                        s=10,
                        facecolors="none",
                        edgecolors="r",
                        linewidths=0.7,
                        marker="o",
                        label="- mode" if first_patch else None,
                        depthshade=False,
                        )
            else:
                ax.plot(
                    g0[:, 0], g0[:, 1],
                    "k.", markersize=6,
                    label="baseline" if first_patch else None,
                )
                ax.plot(
                    gp[:, 0], gp[:, 1],
                    "b.", markersize=5,
                    label="+ mode" if first_patch else None,
                )
                ax.plot(
                    gm[:, 0], gm[:, 1],
                    "r.", markersize=5,
                    label="- mode" if first_patch else None,
                )

            first_patch = False
            offset += jdir * k

        ax.grid(True, alpha=0.15)
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_title(f"Geometric mode {j+1}", fontweight="bold")

        if jdir == 3:
            ax.set_zlabel("z")
            ax.set_xlim(xmin, xmax)
            ax.set_ylim(ymin, ymax)
            ax.set_zlim(zmin, zmax)

            try:
                ax.set_box_aspect((xspan, yspan, zspan))
            except Exception:
                pass

            # closer to a useful default view for streamlined bodies
            ax.view_init(elev=18, azim=-120)

            try:
                ax.dist = 8
            except Exception:
                pass

            ax.legend(loc="best")
        else:
            ax.set_xlim(xmin, xmax)
            ax.set_ylim(ymin, ymax)
            ax.set_aspect("equal", adjustable="box")
            ax.legend(loc="best")

        fig.tight_layout()
        fig.savefig(out / f"mode_{j+1:02d}.png", bbox_inches="tight", dpi=220)
        plt.close(fig)

def save_all_plots(model: PmeModel, outdir: str | Path | None = None, n_modes: int = 3) -> None:
    """Generate the same family of plots currently produced by MATLAB."""
    out = _ensure_outdir(outdir)

    plot_variance_retained(model, out)
    plot_scree_plot(model, out)
    plot_nmse_by_source(model, out)
    plot_variance_by_source(model, out)
    plot_variable_modes(model, out)
    plot_modes(model, out, n_modes=n_modes)
