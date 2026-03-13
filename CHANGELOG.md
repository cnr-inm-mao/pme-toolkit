# Changelog

All notable changes to **PME-toolkit** will be documented in this file.

The format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and semantic versioning principles.

---

## [Unreleased]

### Planned

- Full Python implementation of PME workflow
- Additional benchmark datasets
- Additional validation tests
- Extended dataset packaging and automation
- Additional visualization utilities for:
  - reduced coordinates
  - geometric modes
  - reconstruction accuracy

---

## [1.0.2] – 2026-03-12

### Added

- MATLAB visualization utilities for PME results:
  - `plot_modes`
  - `plot_variable_modes`
  - `plot_variance_retained`
  - `plot_variance_by_source`
  - `plot_nmse_by_source`
  - `plot_scree_plot`
- Centralized color definitions for data sources via `source_colors`
- Extended plotting functionality integrated into `pme/report`

### Improved

- Refactoring of PME visualization utilities to separate plotting logic
  from report generation
- Improved interpretability of PME reductions through dedicated plots
  for:
  - eigenvalue decay (scree plot)
  - variance retention
  - source-wise variance contribution
  - variable contributions to modes
- Improved consistency of MATLAB reporting outputs

### Notes

This patch release improves **post-processing and visualization of PME results** 
without modifying the core PME algorithms.

---

## [1.0.1] – 2026-03-11

### Added

- GitHub public release of **PME-toolkit**
- Zenodo integration with DOI for the software release
- Continuous integration workflow for MATLAB tests
- Automated dataset download support for benchmark datasets
- Repository badges (CI, DOI, MATLAB)

### Improved

- Repository structure stabilized for public distribution
- Documentation organization under `docs/`
- Dataset metadata structure under `databases/`
- Benchmark configuration workflow

### Fixed

- Minor documentation inconsistencies between examples and repository structure
- Dataset download robustness improvements
- Minor fixes in MATLAB benchmark execution scripts

### Notes

This release represents the **first stable public release** of PME-toolkit.

The MATLAB implementation remains the **reference implementation** of the toolkit.

The Python package currently provides infrastructure and configuration utilities
and will progressively reach feature parity with the MATLAB implementation.

---

## [0.1.0] – Initial public release

### Added

- Initial MATLAB implementation of:
  - PME
  - PI-PME
  - PD-PME
- Analytical backmapping from reduced space to original design variables
- JSON-based configuration system for benchmark workflows
- Benchmark definitions under `benchmarks/`
- Dataset metadata structure under `databases/`
- Tiny self-contained glider dataset for repository tests
- MkDocs documentation site
- Python package scaffold
- Python configuration loader and minimal tests
- MATLAB test suite under `tests/`
- JOSS paper draft under `paper/`

### Documentation

- Repository overview and usage in `README.md`
- MATLAB and Python subpackage documentation
- Benchmark and dataset documentation
- MkDocs documentation pages:
  - quickstart
  - configuration specification
  - MATLAB API
  - Python API
  - reproducibility
  - backmapping
  - benchmarks
  - datasets

### Notes

- MATLAB is currently the **reference implementation**.
- Python implementation is **work in progress** and currently limited to infrastructure and tests.
