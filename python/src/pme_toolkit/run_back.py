from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from .config_loader import load_case_json
from .model import PmeModel


def _is_absolute_path(p: str | Path) -> bool:
    return Path(p).expanduser().is_absolute()


def _resolve_path(p: str | Path, base_dir: Path) -> Path:
    p = Path(p).expanduser()
    if p.is_absolute():
        return p.resolve()
    return (base_dir / p).resolve()


def _resolve_outdir_from_case(cfg_case: dict[str, Any], base_dir: Path) -> Path:
    io_cfg = dict(cfg_case.get("io", {}) or {})
    outdir = io_cfg.get("outdir")
    if outdir:
        return _resolve_path(outdir, base_dir)
    return (base_dir / "results_py").resolve()


def _read_vector(path: Path, fmt: str) -> np.ndarray:
    fmt = fmt.lower()

    if fmt == "txt":
        v = np.loadtxt(path, dtype=float)
        return np.asarray(v, dtype=float).reshape(-1)

    if fmt == "csv":
        a = np.loadtxt(path, delimiter=",", dtype=float)
        a = np.asarray(a, dtype=float)
        if a.ndim == 1:
            return a.reshape(-1)
        if a.shape[0] == 1:
            return a.reshape(-1)
        if a.shape[1] == 1:
            return a.reshape(-1)
        raise ValueError(f"CSV input must be a single row or single column: {path}")

    raise ValueError(f"Unknown input format: {fmt} (use txt|csv)")


def _write_vector(path: Path, fmt: str, v: np.ndarray, layout: str) -> None:
    fmt = fmt.lower()
    layout = layout.lower()

    path.parent.mkdir(parents=True, exist_ok=True)
    v = np.asarray(v, dtype=float).reshape(-1)

    if fmt == "txt":
        np.savetxt(path, v.reshape(-1, 1), fmt="%.17g")
        return

    if fmt == "csv":
        if layout == "row":
            np.savetxt(path, v.reshape(1, -1), delimiter=",", fmt="%.17g")
            return
        if layout == "col":
            np.savetxt(path, v.reshape(-1, 1), delimiter=",", fmt="%.17g")
            return
        raise ValueError('output.layout must be "row" or "col" for csv.')

    raise ValueError(f"Unknown output format: {fmt} (use txt|csv)")


def _infer_k(model: PmeModel) -> int:
    return int(model.nconf)


def _alpha_bounds_from_model(model: PmeModel, rule: str, c: float, nconf_use: int) -> tuple[np.ndarray, np.ndarray, str]:
    rule = rule.lower()

    if rule == "minmax":
        alpha_train = np.asarray(model.alpha_train, dtype=float)
        if alpha_train.ndim != 2 or alpha_train.shape[1] < nconf_use:
            raise ValueError("minmax requires alpha_train with at least nconf_use columns")
        amin = np.min(alpha_train[:, :nconf_use], axis=0)
        amax = np.max(alpha_train[:, :nconf_use], axis=0)
        return amin, amax, "minmax"

    if rule == "3sigma":
        eig = np.asarray(model.eigvals_reduced, dtype=float).reshape(-1)
        if eig.size < nconf_use:
            raise ValueError("3sigma requires eigvals_reduced with at least nconf_use elements")
        sig = np.sqrt(np.maximum(eig[:nconf_use], 0.0))
        amin = -c * sig
        amax = +c * sig
        return amin, amax, "3sigma"

    raise ValueError(f"Unknown denorm.rule: {rule} (use minmax|3sigma)")


def _active_block_from_p(mode: str, layout: dict[str, Any], mact: int) -> tuple[int, int]:
    mode = str(mode).lower()

    if mode in ("pme", "pi"):
        i0 = int(layout["D"]["nRows"])
    elif mode == "pd":
        i0 = 0
    else:
        raise ValueError(f"Unknown mode: {mode}")

    i1 = i0 + int(mact)
    return i0, i1


def _reconstruct_standalone(model: PmeModel, alpha_col: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    MATLAB-parity standalone reconstruction:
      Pc_hat = Zr * alpha
      P_hat  = Pc_hat + delta_m + P0
      Uact   = extract active block from P_hat
      Ubase  = denormalize Uact and reinsert into raw baseline
    """
    alpha_col = np.asarray(alpha_col, dtype=float).reshape(-1, 1)
    nconf_use = alpha_col.shape[0]

    zr = np.asarray(model.z_reduced[:, :nconf_use], dtype=float)
    pc_hat = zr @ alpha_col
    p_hat = pc_hat + np.asarray(model.delta_m, dtype=float) + np.asarray(model.p0, dtype=float)

    idx_active = np.asarray(model.uinfo["idx_active"], dtype=int).reshape(-1)
    mact = idx_active.size

    i0, i1 = _active_block_from_p(model.mode, model.layout, mact)
    if i1 > p_hat.shape[0]:
        raise ValueError(f"Active-variable block exceeds P size: stop={i1}, P rows={p_hat.shape[0]}")

    uact_hat = p_hat[i0:i1, 0].reshape(-1)

    urange = model.uinfo.get("Urange")
    if urange is None:
        raise RuntimeError("Missing model.uinfo['Urange'] for active-variable denormalization")

    urange = np.asarray(urange, dtype=float)
    if urange.shape[0] < mact or urange.shape[1] < 2:
        raise RuntimeError("model.uinfo['Urange'] must be at least [Mact x 2]")

    umin = urange[:mact, 0]
    umax = urange[:mact, 1]
    du = umax - umin
    du[np.abs(du) < np.finfo(float).eps] = 1.0

    uact_raw = uact_hat * du + umin

    mbase = int(model.uinfo["Mbase"])
    ubase0 = model.uinfo.get("Ubase_baseline_raw")
    if ubase0 is None:
        raise RuntimeError("Missing model.uinfo['Ubase_baseline_raw']")

    ubase = np.asarray(ubase0, dtype=float).reshape(-1).copy()
    if ubase.size != mbase:
        raise RuntimeError(f"Ubase_baseline_raw length mismatch: expected {mbase}, got {ubase.size}")

    ubase[idx_active] = uact_raw

    return p_hat.reshape(-1), uact_raw.reshape(-1), ubase.reshape(-1), uact_hat.reshape(-1)


def run_back(
    cfg_json: str | Path,
    *,
    x01: np.ndarray | None = None,
    dry_run: bool = False,
    model_file: str | Path | None = None,
    output_file: str | Path | None = None,
) -> dict[str, Any]:
    cfg_json = Path(cfg_json).expanduser().resolve()
    if not cfg_json.is_file():
        raise FileNotFoundError(f"Config JSON not found: {cfg_json}")

    with cfg_json.open("r", encoding="utf-8") as f:
        cfg_bm = json.load(f)

    if "case_json" not in cfg_bm or not str(cfg_bm["case_json"]).strip():
        raise ValueError('backmapping.json must contain "case_json"')

    cfg_dir = cfg_json.parent
    case_json = _resolve_path(cfg_bm["case_json"], cfg_dir)
    if not case_json.is_file():
        raise FileNotFoundError(f"case_json not found: {case_json}")

    cfg_case, case_dir = load_case_json(case_json)
    case_dir = Path(case_dir).resolve()
    outdir = _resolve_outdir_from_case(cfg_case, case_dir)

    if model_file is not None:
        model_path = Path(model_file).expanduser().resolve()
    else:
        run_case_cfg = dict(cfg_bm.get("run_case", {}) or {})
        if run_case_cfg.get("model_file"):
            model_path = _resolve_path(run_case_cfg["model_file"], case_dir)
        else:
            model_path = (outdir / "model.npz").resolve()

    if not model_path.is_file():
        raise FileNotFoundError(f"Model file not found: {model_path}. Run pme-run on the case first.")

    model = PmeModel.load(model_path)

    if x01 is not None:
        x01_vec = np.asarray(x01, dtype=float).reshape(-1)
        x01_file_meta = "(override)"
    else:
        input_cfg = dict(cfg_bm.get("input", {}) or {})
        if not input_cfg.get("file"):
            raise ValueError('backmapping.json must contain "input.file" (or provide x01 override)')
        in_file = _resolve_path(input_cfg["file"], case_dir)
        in_fmt = str(input_cfg.get("format", "txt")).lower()
        x01_vec = _read_vector(in_file, in_fmt)
        x01_file_meta = str(in_file)

    k_model = _infer_k(model)
    nconf_use = int(dict(cfg_bm.get("reduced_space", {}) or {}).get("nconf", k_model))
    if nconf_use < 1 or nconf_use > k_model:
        raise ValueError(f"reduced_space.nconf must be between 1 and {k_model} (got {nconf_use})")

    if x01_vec.size != nconf_use:
        raise ValueError(f"x01 length must be nconf_use={nconf_use} (got {x01_vec.size})")
    if not np.all(np.isfinite(x01_vec)):
        raise ValueError("x01 contains NaN/Inf")
    if not np.all((x01_vec >= 0.0) & (x01_vec <= 1.0)):
        raise ValueError("x01 must be in [0,1]")

    denorm_cfg = dict(cfg_bm.get("denorm", {}) or {})
    rule = str(denorm_cfg.get("rule", "3sigma")).lower()
    c = float(denorm_cfg.get("c", 3.0))

    amin, amax, rule_used = _alpha_bounds_from_model(model, rule, c, nconf_use)
    alpha_col = amin + x01_vec * (amax - amin)

    p_hat = np.array([])
    uact_raw = np.array([])
    ubase = np.array([])

    if not dry_run:
        p_hat, uact_raw, ubase, _ = _reconstruct_standalone(model, alpha_col)

    output_cfg = dict(cfg_bm.get("output", {}) or {})
    what = str(output_cfg.get("what", "Ubase"))

    if what.lower() == "ubase":
        u = ubase
    elif what.lower() == "uact":
        u = uact_raw
    elif what.lower() == "p":
        u = p_hat
    elif what.lower() == "alpha":
        u = alpha_col.reshape(-1)
    else:
        raise ValueError(f'Unsupported output.what="{what}". Use Ubase, Uact, P, or alpha.')

    if output_file is not None:
        out_file = Path(output_file).expanduser().resolve()
    else:
        if not output_cfg.get("file"):
            raise ValueError("output.file is required")
        out_file = _resolve_path(output_cfg["file"], case_dir)

    out_fmt = str(output_cfg.get("format", "txt")).lower()
    out_layout = str(output_cfg.get("layout", "col")).lower()
    write_meta = bool(output_cfg.get("write_meta", True))

    written = {"vector_file": "", "meta_file": ""}

    if not dry_run:
        tmp = out_file.with_suffix(out_file.suffix + ".tmp")
        _write_vector(tmp, out_fmt, u, out_layout)
        tmp.replace(out_file)
        written["vector_file"] = str(out_file)

        if write_meta:
            meta = {
                "schema": "pme.backmapping.v1",
                "case_json": str(case_json),
                "model_file": str(model_path),
                "what": what,
                "nconf_model": k_model,
                "nconf_use": nconf_use,
                "m": int(np.asarray(u).reshape(-1).size),
                "denorm": {"rule": rule_used, "c": c},
                "x01_file": x01_file_meta,
                "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            }

            meta_file = out_file.with_name(out_file.name + ".meta.json")
            with meta_file.open("w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)
            written["meta_file"] = str(meta_file)

    out = {
        "case_dir": str(case_dir),
        "outdir": str(outdir),
        "model_file": str(model_path),
        "x01": x01_vec.reshape(-1),
        "alpha": alpha_col.reshape(-1),
        "P": p_hat.reshape(-1),
        "Uact": uact_raw.reshape(-1),
        "U": np.asarray(u, dtype=float).reshape(-1),
        "written_files": written,
    }

    if not dry_run:
        print(f"[pme.backmap] wrote {out_file} ({out_fmt})")

    return out


def _build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Standalone backmapping from reduced variables to original variables"
    )
    parser.add_argument(
        "cfg_json",
        type=str,
        help="Path to backmapping.json",
    )
    parser.add_argument(
        "--x01",
        type=float,
        nargs="*",
        default=None,
        help="Optional reduced vector override in [0,1]^k",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write output files",
    )
    parser.add_argument(
        "--model-file",
        type=str,
        default=None,
        help="Optional model file override",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default=None,
        help="Optional output file override",
    )
    return parser


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()

    x01 = None if args.x01 is None or len(args.x01) == 0 else np.asarray(args.x01, dtype=float)

    run_back(
        args.cfg_json,
        x01=x01,
        dry_run=bool(args.dry_run),
        model_file=args.model_file,
        output_file=args.output_file,
    )


if __name__ == "__main__":
    main()
