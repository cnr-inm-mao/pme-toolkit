from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path
from typing import Any
from urllib.request import urlopen


def _resolve_required_paths(cfg: dict[str, Any]) -> tuple[Path | None, Path | None]:
    io_cfg = dict(cfg.get("io", {}) or {})
    vars_cfg = dict(cfg.get("vars", {}) or {})

    dbfile = io_cfg.get("dbfile")
    urange_file = vars_cfg.get("Urange_file")

    db_path = Path(dbfile).expanduser().resolve() if dbfile else None
    ur_path = Path(urange_file).expanduser().resolve() if urange_file else None

    return db_path, ur_path


def _all_required_exist(cfg: dict[str, Any]) -> tuple[bool, list[str]]:
    db_path, ur_path = _resolve_required_paths(cfg)

    missing: list[str] = []

    if db_path is None or not db_path.is_file():
        missing.append("dbfile")

    if ur_path is not None and not ur_path.is_file():
        missing.append("Urange_file")

    return len(missing) == 0, missing


def _candidate_dataset_json_paths(cfg: dict[str, Any], base_dir: Path) -> list[Path]:
    """
    Search for dataset.json in the most relevant locations.

    Priority:
    1. case directory and its parents
    2. parent directories of the expected dbfile path
    3. parent directories of the expected Urange_file path
    """
    candidates: list[Path] = []

    # ---------------------------------------------------------
    # (A) walk upward from the case directory
    # ---------------------------------------------------------
    cur = base_dir.resolve()
    for parent in [cur] + list(cur.parents):
        p = parent / "dataset.json"
        if p.is_file():
            candidates.append(p)

    # ---------------------------------------------------------
    # (B) walk upward from expected dbfile location
    # ---------------------------------------------------------
    db_path, ur_path = _resolve_required_paths(cfg)

    if db_path is not None:
        for parent in [db_path.parent] + list(db_path.parent.parents):
            p = parent / "dataset.json"
            if p.is_file():
                candidates.append(p)

    # ---------------------------------------------------------
    # (C) walk upward from expected Urange_file location
    # ---------------------------------------------------------
    if ur_path is not None:
        for parent in [ur_path.parent] + list(ur_path.parent.parents):
            p = parent / "dataset.json"
            if p.is_file():
                candidates.append(p)

    # unique while preserving order
    uniq: list[Path] = []
    seen = set()
    for p in candidates:
        rp = p.resolve()
        if rp not in seen:
            uniq.append(rp)
            seen.add(rp)

    return uniq

def _load_dataset_json(dataset_json: Path) -> dict[str, Any]:
    data = json.loads(dataset_json.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"dataset.json must decode to a JSON object: {dataset_json}")
    return data


def _resolve_dataset_dir(meta: dict[str, Any], dataset_json: Path) -> Path:
    """
    Decide where the shared dataset lives.

    Priority:
    1. meta["shared_dataset_dir"]
    2. directory containing dataset.json
    """
    shared = meta.get("shared_dataset_dir")
    if shared:
        return Path(shared).expanduser().resolve()

    return dataset_json.parent.resolve()


def _download_with_progress(url: str, dst: Path) -> None:
    print(f"[dataset] archive url: {url}")
    print("[dataset] downloading archive...")

    with urlopen(url) as response:
        total = response.headers.get("Content-Length")
        total_bytes = int(total) if total is not None else None

        if total_bytes is not None:
            size_mb = total_bytes / (1024 * 1024)
            print(f"[dataset] size {size_mb:.1f} MB")

        dst.parent.mkdir(parents=True, exist_ok=True)

        chunk_size = 1024 * 1024
        downloaded = 0

        with dst.open("wb") as f:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)

                if total_bytes:
                    pct = 100.0 * downloaded / total_bytes
                    dl_mb = downloaded / (1024 * 1024)
                    tot_mb = total_bytes / (1024 * 1024)
                    print(f"[dataset] downloaded {pct:6.2f} % ({dl_mb:.1f} / {tot_mb:.1f} MB)")
                else:
                    dl_mb = downloaded / (1024 * 1024)
                    print(f"[dataset] downloaded {dl_mb:.1f} MB")

    print(f"[dataset] archive saved to: {dst}")


def _extract_archive(archive_path: Path, dataset_dir: Path) -> None:
    print("[dataset] extracting archive...")
    with zipfile.ZipFile(archive_path, "r") as zf:
        zf.extractall(dataset_dir)
    print(f"[dataset] extracted to: {dataset_dir}")


def _flatten_extracted_tree(dataset_dir: Path) -> None:
    """
    Move .mat/.txt/.json files from nested folders into dataset_dir when needed.
    This mirrors the MATLAB behavior of tolerating archives with an extra top-level folder.
    """
    movable_suffixes = {".mat", ".txt", ".json", ".csv"}

    nested_files = []
    for p in dataset_dir.rglob("*"):
        if not p.is_file():
            continue
        if p.parent == dataset_dir:
            continue
        if p.suffix.lower() in movable_suffixes:
            nested_files.append(p)

    if not nested_files:
        return

    print("[dataset] flattening extracted files...")
    for src in nested_files:
        dst = dataset_dir / src.name
        if dst.exists():
            continue
        shutil.move(str(src), str(dst))

    # attempt to remove empty directories
    for p in sorted(dataset_dir.rglob("*"), reverse=True):
        if p.is_dir():
            try:
                p.rmdir()
            except OSError:
                pass


def _find_dataset_json_or_raise(cfg: dict[str, Any], base_dir: Path) -> Path:
    candidates = _candidate_dataset_json_paths(cfg, base_dir)
    if not candidates:
        raise FileNotFoundError(
            "[dataset] dataset.json not found near case directory or expected dataset paths: "
            f"{base_dir}"
        )
    return candidates[0]

def ensure_case_inputs(cfg: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    """
    Ensure that dbfile and Urange_file exist.

    If they are missing, try to recover them from dataset.json by:
    - reading archive_url / archive_name
    - downloading the archive
    - extracting it
    - flattening extracted files
    - rechecking inputs

    Returns
    -------
    meta : dict
        Dataset metadata actually used (possibly empty if no download needed).
    """
    ok, missing = _all_required_exist(cfg)
    if ok:
        print("[dataset] all required inputs already available.")
        return {}

    print(f"[dataset] missing inputs detected: {', '.join(missing)}")

    dataset_json = _find_dataset_json_or_raise(cfg, base_dir)
    meta = _load_dataset_json(dataset_json)

    dataset_dir = _resolve_dataset_dir(meta, dataset_json)
    dataset_dir.mkdir(parents=True, exist_ok=True)

    print(f"[dataset] shared dataset directory: {dataset_dir}")

    download = dict(meta.get("download", {}) or {})

    archive_url = meta.get("archive_url")
    if not archive_url:
        archive_url = download.get("archive_url")

    archive_name = meta.get("archive_name")
    if not archive_name:
        archive_name = download.get("archive_name")

    if not archive_url:
        raise FileNotFoundError(
            "[dataset] required inputs are missing and dataset.json does not define archive_url "
            "(neither at top level nor under 'download')"
        )

    if not archive_name:
        archive_name = Path(str(archive_url)).name or "dataset_archive.zip"


    archive_path = dataset_dir / str(archive_name)

    if not archive_path.is_file():
        _download_with_progress(str(archive_url), archive_path)
    else:
        print(f"[dataset] archive already available: {archive_path}")

    _extract_archive(archive_path, dataset_dir)
    _flatten_extracted_tree(dataset_dir)

    ok_after, missing_after = _all_required_exist(cfg)
    if not ok_after:
        raise FileNotFoundError(
            "[dataset] archive extracted but required inputs are still missing: "
            + ", ".join(missing_after)
        )

    print("[dataset] required inputs successfully restored.")
    return meta
