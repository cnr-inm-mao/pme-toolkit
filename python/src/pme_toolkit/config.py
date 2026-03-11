from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple


def _resolve_path(base_dir: Path, p: str | None) -> str | None:
    if not p:
        return None
    pp = Path(p)
    if pp.is_absolute():
        return str(pp)
    # If user provided an existing relative path from CWD, keep it.
    if pp.exists():
        return str(pp.resolve())
    return str((base_dir / pp).resolve())


def load_case_json(case_json: str | Path) -> Tuple[Dict[str, Any], Path]:
    """Load a case JSON and resolve relative paths w.r.t. the JSON directory.

    Returns:
        cfg: dict
        base_dir: Path (directory containing the case.json)

    Conventions:
        - All file paths inside cfg are resolved relative to the folder that contains the JSON.
        - This function does not attempt to fully validate the schema (kept lightweight).
    """
    case_path = Path(case_json).expanduser().resolve()
    if not case_path.is_file():
        raise FileNotFoundError(f"case.json not found: {case_path}")

    base_dir = case_path.parent
    cfg = json.loads(case_path.read_text(encoding="utf-8"))

    # Resolve common I/O paths
    io = cfg.get("io", {})
    if isinstance(io, dict):
        if "dbfile" in io:
            io["dbfile"] = _resolve_path(base_dir, io.get("dbfile"))
        if "outdir" in io:
            io["outdir"] = _resolve_path(base_dir, io.get("outdir"))
        cfg["io"] = io

    vars_ = cfg.get("vars", {})
    if isinstance(vars_, dict):
        if "Urange_file" in vars_:
            vars_["Urange_file"] = _resolve_path(base_dir, vars_.get("Urange_file"))
        cfg["vars"] = vars_

    return cfg, base_dir
