# Changelog

All notable changes to **PME-toolkit** will be documented in this file.

The format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and semantic versioning principles.

---

## [Unreleased]

### Planned

- Documentation refinement for the public `v1.2.x` release
- README alignment across top-level, MATLAB, Python, benchmarks, and datasets
- Additional regression-style validation between MATLAB and Python outputs
- Further packaging and release cleanup for JOSS readiness
- Expanded benchmark coverage and dataset publication workflow

---

## [1.2.0] – 2026-03-17

### Added

- Functional Python implementation of the PME-toolkit workflow for:
  - `PME`
  - `PI-PME`
  - `PD-PME`
- Python case runner:
  - `pme_toolkit.run_case`
  - console entry point `pme-run`
- Python standalone backmapping workflow:
  - `pme_toolkit.run_back`
  - console entry point `pme-back`
- Python model persistence through `model.npz`
- Python standalone backmapping metadata output with schema:
  - `pme.backmapping.v1`
- Python support for reduced-space input `x01`:
  - override from command line
  - input from file
  - `txt` and `csv` formats
  - row/column vector handling
- Python tests for:
  - configuration loading
  - core PME fitting on the tiny glider dataset
  - repository-style `run_case` workflow
  - standalone backmapping workflow
- Alignment of MATLAB and Python test workflows to a common results directory:
  - `tests/cases/results`

### Changed

- Python package status moved from scaffold/infrastructure stage to a usable workflow implementation
- Python `run_case` output logic aligned with repository-style case execution
- Python outputs simplified to save only:
  - `report.mat`
  - `model.npz`
  instead of Python-specific extra artifacts
- Python backmapping redesigned to behave as a standalone workflow:
  - it now reads a previously saved model
  - it no longer refits PME during backmapping
- Python reconstruction of full design variables aligned with MATLAB logic by reinserting active variables into the raw baseline parameter vector
- MATLAB test outputs were aligned with Python test outputs so that both workflows use:
  - `tests/cases/results`

### Improved

- Cross-language consistency between MATLAB and Python for:
  - case execution
  - backmapping conventions
  - output directory structure
  - metadata structure for backmapping results
- Python package metadata and CLI exposure through `pyproject.toml`
- Python package initialization and exported API cleanup
- Consistency of local repository tests for the tiny glider case
- Release readiness of the Python side for a dual MATLAB/Python public version

### Fixed

- Incorrect or outdated Python status in packaging/documentation metadata
- Python backmapping failures caused by:
  - missing standalone model persistence
  - inconsistent reduced-space dimensionality handling
  - inconsistent reinsertion of fixed variables
  - mismatch between backmapping input schema and repository test cases
- Python editable installation and command-line entry point issues
- Test mismatches caused by outdated expected output filenames
- Inconsistent MATLAB/Python test result paths

### Notes

This release marks the first **dual MATLAB/Python public workflow release** of PME-toolkit.

MATLAB remains the **reference implementation** for algorithm validation and numerical behaviour.

Python now provides a working repository-style implementation of:
- PME
- PI-PME
- PD-PME
- case execution
- standalone backmapping
- package installation and CLI entry points

Model serialization remains language-specific:
- MATLAB saves `model.mat`
- Python saves `model.npz`

This choice preserves practical workflow parity without forcing fragile binary compatibility between the two implementations.

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
