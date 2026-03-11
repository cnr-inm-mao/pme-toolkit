"""PME Toolkit (Python).

The MATLAB implementation under `matlab/src/+pme` is the reference.
This Python package provides a consistent interface and shared JSON input handling.
"""

from .config import load_case_json

__all__ = ["load_case_json"]
