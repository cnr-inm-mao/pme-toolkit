from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from .config_loader import load_case_json
from .filters import apply_filters
from .io import load_mat_database, load_mat_range
from .model import fit_pme
from .plotting import save_all_plots
from .report import build_report, print_report
from .datasets import ensure_case_inputs


def _json_default(obj: Any) -> Any:
    """JSON serializer helper for numpy/path objects."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, Path):
        return str(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _resolve_outdir(cfg: dict[str, Any], base_dir: Path, outdir_override: str | Path | None = None) -> Path:
    """
    Resolve output directory.

    Priority:
    1. explicit override
    2. cfg["io"]["outdir"] if present
    3. <case_dir>/results_py
    """
    if outdir_override is not None:
        return Path(outdir_override).expanduser().resolve()

    io_cfg = dict(cfg.get("io", {}) or {})
    outdir = io_cfg.get("outdir")

    if outdir:
        return Path(outdir).expanduser().resolve()

    return (base_dir / "results_py").resolve()


def _save_report_json(report: dict[str, Any], outdir: Path) -> Path:
    path = outdir / "report.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=_json_default)
    return path


def _save_results_npz(model: Any, report: dict[str, Any], outdir: Path) -> Path:
    """Save compact numerical results in NPZ form."""
    path = outdir / "pme_results.npz"

    np.savez_compressed(
        path,
        eigvals_full=np.asarray(model.eigvals_full, dtype=float),
        eigvals_reduced=np.asarray(model.eigvals_reduced, dtype=float),
        z_full=np.asarray(model.z_full, dtype=float),
        z_reduced=np.asarray(model.z_reduced, dtype=float),
        alpha_train=np.asarray(model.alpha_train, dtype=float),
        p0=np.asarray(model.p0, dtype=float),
        delta_m=np.asarray(model.delta_m, dtype=float),
        pc=np.asarray(model.pc, dtype=float),
        w=np.asarray(model.w, dtype=float),
        filter_mask=np.asarray(model.filter_mask, dtype=bool),
        nmse_geom_by_k=np.asarray(report["nmse"].get("geom_by_k", []), dtype=float),
        nconf=np.asarray([model.nconf], dtype=int),
        mact=np.asarray([model.uinfo["Mact"]], dtype=int),
        db_used_rows=np.asarray([model.db_used_shape[0]], dtype=int),
        db_used_cols=np.asarray([model.db_used_shape[1]], dtype=int),
    )
    return path


def _save_manifest(
    case_json: Path,
    cfg: dict[str, Any],
    outdir: Path,
    report_path: Path,
    npz_path: Path,
) -> Path:
    manifest = {
        "case_json": str(case_json),
        "mode": cfg.get("mode"),
        "outdir": str(outdir),
        "artifacts": {
            "report_json": str(report_path),
            "results_npz": str(npz_path),
            "plots": [
                str(outdir / "scree_plot.png"),
                str(outdir / "variance_retained.png"),
                str(outdir / "nmse_by_source.png"),
                str(outdir / "variance_by_source.png"),
                str(outdir / "variable_modes_normalized.png"),
            ],
        },
    }

    path = outdir / "manifest.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return path


def run_case(
    case_json: str | Path,
    *,
    save_plots: bool = True,
    n_modes_plot: int = 3,
    print_text_report: bool = True,
    outdir_override: str | Path | None = None,
) -> dict[str, Any]:
    """
    Run a repository-style case in Python, following MATLAB orchestration as closely as possible.

    Current scope:
    - read case.json
    - dataset presence check
    - load DB and Urange
    - apply preprocessing filters
    - fit model on DB_used
    - print report
    - save plots
    - save JSON/NPZ artifacts
    """
    case_path = Path(case_json).expanduser().resolve()
    cfg, base_dir = load_case_json(case_path)

    dataset_meta = ensure_case_inputs(cfg, base_dir)

    io_cfg = dict(cfg.get("io", {}) or {})
    vars_cfg = dict(cfg.get("vars", {}) or {})

    dbfile = io_cfg.get("dbfile")
    if not dbfile:
        raise ValueError("cfg.io.dbfile is required")

    db = load_mat_database(dbfile)

    urange_file = vars_cfg.get("Urange_file")
    urange = load_mat_range(urange_file) if urange_file else None

    # layout is needed by filters, but fit_pme already computes it internally.
    # To avoid duplicating parse_layout import here, retrieve it through model module logic:
    from .layout import parse_layout
    layout = parse_layout(cfg)

    filt = apply_filters(db, cfg, layout)
    db_used = filt.db_used

    print(f"[run_case] filters cumulative kept {filt.info['total_kept']} / {filt.info['Ns_total']} samples")

    model = fit_pme(
        db_used,
        cfg,
        urange_full=urange,
        filter_mask=filt.mask,
        filter_info=filt.info,
        db_total_shape=db.shape,
    )

    if print_text_report:
        report = print_report(model)
    else:
        report = build_report(model)

    outdir = _resolve_outdir(cfg, base_dir, outdir_override=outdir_override)
    outdir.mkdir(parents=True, exist_ok=True)

    if save_plots:
        save_all_plots(model, outdir=outdir, n_modes=n_modes_plot)

    report_path = _save_report_json(report, outdir)
    npz_path = _save_results_npz(model, report, outdir)
    manifest_path = _save_manifest(case_path, cfg, outdir, report_path, npz_path)

    saved = {
        "report_json": str(report_path),
        "results_npz": str(npz_path),
        "manifest_json": str(manifest_path),
    }

    print()
    print(f"[run_case.py] output directory: {outdir}")
    print(f"[run_case.py] saved report:     {report_path.name}")
    print(f"[run_case.py] saved results:    {npz_path.name}")
    if save_plots:
        print("[run_case.py] saved plots:      scree_plot.png, variance_retained.png, "
              "nmse_by_source.png, variance_by_source.png, "
              "variable_modes_normalized.png, mode_XX.png")

    return {
        "cfg": cfg,
        "layout": layout,
        "meta": dataset_meta,
        "case_json": str(case_path),
        "DB": db,
        "DB_used": db_used,
        "model": model,
        "report": report,
        "outdir": str(outdir),
        "saved": saved,
        "filter_info": filt.info,
        "filter_mask": filt.mask,
    }


def _build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a PME-toolkit Python case from a repository-style case.json"
    )
    parser.add_argument(
        "case_json",
        type=str,
        help="Path to case.json",
    )
    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Do not generate plots",
    )
    parser.add_argument(
        "--n-modes-plot",
        type=int,
        default=3,
        help="Number of geometric modes to plot",
    )
    parser.add_argument(
        "--quiet-report",
        action="store_true",
        help="Do not print the textual report to stdout",
    )
    parser.add_argument(
        "--outdir",
        type=str,
        default=None,
        help="Optional output directory override",
    )
    return parser


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()

    run_case(
        args.case_json,
        save_plots=not args.no_plots,
        n_modes_plot=int(args.n_modes_plot),
        print_text_report=not args.quiet_report,
        outdir_override=args.outdir,
    )


if __name__ == "__main__":
    main()
