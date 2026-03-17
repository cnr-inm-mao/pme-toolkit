"""
PME-toolkit Python package.

This package provides the Python implementation of the PME-toolkit
workflow, including PME, PI-PME, and PD-PME utilities.

The MATLAB implementation remains the project reference implementation.
"""

from .config_loader import load_case_json, load_config
from .layout import parse_layout
from .io import load_mat_database, load_mat_range
from .model import PmeModel, fit_from_case, fit_model, fit_pme
from .report import build_report, print_report
from .plotting import (
    plot_scree_plot,
    plot_variance_retained,
    plot_nmse_by_source,
    plot_variance_by_source,
    plot_variable_modes,
    plot_modes,
    save_all_plots,
    source_colors,
)
from .filters import apply_filters, FilterResult
from .weights import build_weights, build_wf, build_wc
from .datasets import ensure_case_inputs

__all__ = [
    "load_case_json",
    "load_config",
    "parse_layout",
    "load_mat_database",
    "load_mat_range",
    "PmeModel",
    "fit_model",
    "fit_pme",
    "fit_from_case",
    "build_report",
    "print_report",
    "plot_scree_plot",
    "plot_variance_retained",
    "plot_nmse_by_source",
    "plot_variance_by_source",
    "plot_variable_modes",
    "plot_modes",
    "save_all_plots",
    "source_colors",
    "apply_filters",
    "FilterResult",
    "build_weights",
    "build_wf",
    "build_wc",
    "ensure_case_inputs",
]
