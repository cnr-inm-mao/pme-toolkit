# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project follows [Semantic Versioning](https://semver.org/).

---

## [1.0.1] – 2026-03-11

### Added
- First public release of **PME-toolkit**.
- MATLAB reference implementation of:
  - Parametric Model Embedding (PME)
  - Physics-Informed PME (PI-PME)
  - Physics-Driven PME (PD-PME)
- Backmapping workflow for reconstruction of geometries from reduced coordinates.
- Benchmark framework for evaluating design-space dimensionality reduction methods.
- Initial benchmark cases including the **bio-inspired underwater glider dataset**.
- Automatic dataset download from **Zenodo** when required datasets are missing.
- MATLAB automated tests and continuous integration using GitHub Actions.
- Initial Python package scaffold to support future feature-parity implementation.
- GitHub Pages documentation with guides on:
  - PME methodology
  - workflow usage
  - datasets and benchmarks
  - backmapping.
- Citation metadata (`CITATION.cff`) and Zenodo DOI integration.
- Contributing guidelines and project roadmap.

### Changed
- Repository structure reorganized to clearly separate:
  - `matlab/` implementation
  - `python/` implementation
  - `benchmarks/`
  - `databases/`
  - `docs/`
- Unified configuration workflow for running benchmark cases.
- Improved dataset management through centralized dataset metadata.
- Updated README with installation instructions and quick start example.
- Documentation expanded with detailed explanations of PME variants and workflows.

### Fixed
- Various documentation inconsistencies between examples and repository structure.
- Improved robustness of dataset download and extraction utilities.
- Minor corrections in MATLAB scripts for benchmark execution.

### Notes
This release establishes the **MATLAB implementation as the reference implementation**
of the PME-toolkit.

The **Python implementation is currently under development** and provides the
initial package structure to support future feature-parity with the MATLAB version.

---

## [Unreleased]

### Planned
- Full Python implementation of the PME workflow.
- Additional benchmark datasets (e.g., NACA airfoil datasets).
- Extended visualization utilities for:
  - modal shapes
  - reduced-coordinate distributions
  - reconstruction accuracy.
- Additional benchmark problems and comparative evaluation tools.
