from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _resolve_path(base_dir: Path, value: str | None) -> str | None:
    """Resolve a possibly-relative path against the case.json directory."""
    if value is None or value == "":
        return None

    path = Path(value).expanduser()
    if path.is_absolute():
        return str(path.resolve())

    return str((base_dir / path).resolve())


def _resolve_case_paths(cfg: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    """Resolve the path-like fields used by the current repository schema."""
    out = dict(cfg)

    io_cfg = dict(out.get("io", {}) or {})
    if "dbfile" in io_cfg:
        io_cfg["dbfile"] = _resolve_path(base_dir, io_cfg.get("dbfile"))
    if "outdir" in io_cfg and io_cfg.get("outdir"):
        io_cfg["outdir"] = _resolve_path(base_dir, io_cfg.get("outdir"))
    out["io"] = io_cfg

    vars_cfg = dict(out.get("vars", {}) or {})
    if "Urange_file" in vars_cfg:
        vars_cfg["Urange_file"] = _resolve_path(base_dir, vars_cfg.get("Urange_file"))
    out["vars"] = vars_cfg

    return out


def load_case_json(case_json: str | Path) -> tuple[dict[str, Any], Path]:
    """Load a case.json file and resolve repository-relative paths.

    Returns
    -------
    cfg
        Parsed JSON configuration with resolved paths.
    base_dir
        Directory containing case.json.
    """
    case_path = Path(case_json).expanduser().resolve()
    if not case_path.is_file():
        raise FileNotFoundError(f"case.json not found: {case_path}")

    cfg = json.loads(case_path.read_text(encoding="utf-8"))
    if not isinstance(cfg, dict):
        raise TypeError("case.json must decode to a JSON object")

    base_dir = case_path.parent
    cfg = _resolve_case_paths(cfg, base_dir)

    return cfg, base_dir


def load_config(case_json: str | Path) -> dict[str, Any]:
    """Compatibility wrapper for the earlier scaffold test."""
    cfg, _ = load_case_json(case_json)
    return cfg
