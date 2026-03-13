"""PME-toolkit Python package.

This package provides the Python-side implementation of the PME workflow.

Current status:
- PME core: implemented in a first stable offline form
- PI-PME: TODO
- PD-PME: TODO

The MATLAB implementation remains the project reference implementation.
"""

from .config_loader import load_case_json, load_config
from .layout import parse_layout
from .io import load_mat_database, load_mat_range
from .model import PmeModel, fit_from_case, fit_pme
from .report import build_report, print_report

__all__ = [
    "load_case_json",
    "load_config",
    "parse_layout",
    "load_mat_database",
    "load_mat_range",
    "PmeModel",
    "fit_pme",
    "fit_from_case",
    "build_report",
    "print_report",
]
