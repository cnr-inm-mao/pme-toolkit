from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_case_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pme-run",
        description="PME Toolkit runner (Python). Loads the common case.json and prints resolved paths.",
    )
    parser.add_argument("case_json", type=str, help="Path to case.json")
    args = parser.parse_args(argv)

    cfg, base = load_case_json(args.case_json)

    print("PME Toolkit (Python)\n")
    print(f"case.json : {Path(args.case_json).resolve()}")
    print(f"base_dir : {base}")

    io = cfg.get("io", {})
    if isinstance(io, dict):
        print("\nResolved I/O")
        for k in ("dbfile", "outdir"):
            if k in io:
                print(f"  {k}: {io[k]}")

    vars_ = cfg.get("vars", {})
    if isinstance(vars_, dict) and vars_.get("Urange_file"):
        print(f"\nResolved vars.Urange_file: {vars_['Urange_file']}")

    print("\nNote: the MATLAB implementation is the reference runner (pme.run_case).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
