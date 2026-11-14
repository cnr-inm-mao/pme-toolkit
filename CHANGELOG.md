# Changelog

All notable changes to **PME-toolkit** will be documented in this file.

The format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and semantic versioning principles.

---

## [1.3.0] - Unreleased

### Added

- Symmetric snapshot Gram eigensolvers for PME, PI-PME and PD-PME in both
  MATLAB and Python, building on Antoine DeBlois's
  [PR #1](https://github.com/cnr-inm-mao/pme-toolkit/pull/1). The complete
  lifted modes retain the zero-weight native components used by backmapping.
- Vector weight storage and bounded row-block Gram assembly, avoiding dense
  weight matrices. The regular case workflow keeps construction data in memory.
- `solver="auto"|"direct"|"snapshot"` in both languages. The default `auto`
  chooses the smaller symmetric eigenproblem; direct fitting operates only
  on positive-weight observation rows and recovers native modes separately.
- True row-reader snapshot fitting, native-only compact models, optional
  observation-mode writers, and cross-Gram query projection in both languages.
  Streaming centers each observation using the construction samples and keeps
  the source metric fixed across storage blocks.
- Shared `snapshot` options for numerical rank, absolute and relative
  eigenvalue cutoffs, repeated-eigenvalue clusters and row-block size.
- Controlled-spectrum direct-reference tests and a common PME/PI/PD fixture
  for comparison of current MATLAB and Python outputs in CI.
- Regression against the unchanged pre-snapshot implementation on the complete
  Zenodo airfoil database, covering PME, PI-PME and PD-PME, with actual MATLAB
  and Python comparison in a dedicated workflow.
- A reproducible manuscript verification driver and shared curve inputs for
  the 1,048,576-coordinate streamed fit and analytical native backmapping.

### Changed

- Replace the augmented nonsymmetric direct eigensolve with a symmetric
  solve on positive-weight observations. Direct and snapshot are two solvers
  within one fitting pipeline, with shared rank and variance-selection rules;
  the previous direct code is used only from a pinned regression revision.
- Make the public dense weight builders compatibility wrappers over the
  diagonal builders in both languages, keeping one source-weight implementation.
- Lift only resolved positive modes and keep complete eigenvalue clusters at
  the automatic retention boundary. Datasets with no resolved positive
  weighted variance now raise a clear error.
- Measure confidence and global variance retention against the full Gram
  trace, including variance excluded by numerical rank truncation. An
  unattainable confidence target produces a warning and achieved-retention
  diagnostics.
- Store `model.W`/`model.w` as a diagonal vector in newly fitted models.
  Legacy dense saved weights remain supported. Explicit dense weight-builder
  functions are retained for compatibility. Full-spectrum diagnostic arrays
  now contain only the resolved positive spectrum.
- Compute global reconstruction NMSE from weighted residual energy. Constant
  sources contribute no retained variance, and diagnostic curves include
  the selected dimension even when it exceeds the number of native variables.

### Fixed

- Reject PI/PD configurations without physical fields or scalars in both
  MATLAB and Python ([#4](https://github.com/cnr-inm-mao/pme-toolkit/issues/4),
  reported by Kazuko Fuchi). Previously, default empty physics blocks could
  let PI-PME run as geometry-only PME. Validation now runs before case data
  loading/downloads and in direct fitting calls. Regression tests cover
  invalid configurations, valid field-only/scalar-only cases, and standard
  PME without physics.
- Qualify MATLAB's `pme.slice` call in direct model transformation.

### Scope

- The standard case loader continues to read its database into memory. The
  advanced streaming API accepts replayable observation and weight readers,
  so procedural, mapped, or file-backed data can be processed without loading
  the complete observation matrix. Source-specific normalization is fixed
  before fitting, using a preliminary pass when needed.
- See [Snapshot formulation](docs/snapshot.md) for equations, compatibility
  changes, conditioning, solver selection, and the two storage models.

### Planned

- Synchronize website pages and docs text with the actual dual MATLAB/Python status of the repository
- Extend cross-language regression coverage beyond the tiny glider case
- Broaden benchmark/test coverage for PME, PI-PME, and PD-PME cases
- Further refine JOSS-facing documentation and review readiness material
- Consolidate packaging, release, and citation workflows after the first PyPI/JOSS cycle

---

## [1.2.0] – 2026-03-17

### Added

- First public **dual MATLAB/Python workflow release** of PME-toolkit
- Functional Python implementation for:
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
- Python standalone backmapping metadata output with schema `pme.backmapping.v1`
- Python support for reduced-space input `x01` from command line and file (`txt`, `csv`, row/column vector handling)
- Python tests covering:
  - configuration loading
  - core PME fitting on the tiny glider dataset
  - repository-style `run_case` workflow
  - standalone backmapping workflow
- Alignment of MATLAB and Python test workflows to a shared results directory: `tests/cases/results`
- PyPI packaging metadata and console-script exposure through `pyproject.toml`
- Public PyPI distribution of the package
- Zenodo-linked public software release for version `v1.2`

### Changed

- Python package status moved from scaffold/infrastructure stage to a usable workflow implementation
- Python `run_case` output logic aligned with repository-style case execution
- Python outputs simplified to save only:
  - `report.mat`
  - `model.npz`
- Python backmapping redesigned as a standalone workflow reading a previously saved model instead of refitting PME
- Python reconstruction of full design variables aligned with MATLAB logic by reinserting active variables into the raw baseline parameter vector
- MATLAB test outputs aligned with Python outputs so that both workflows use `tests/cases/results`
- Top-level repository status updated to a real dual-language release, no longer MATLAB-only in public packaging terms

### Improved

- Cross-language consistency between MATLAB and Python for:
  - case execution
  - backmapping conventions
  - output directory structure
  - metadata conventions for backmapping results
- Release readiness of the Python side for a public versioned distribution
- Installability and command-line usability for external users through PyPI
- Public dissemination readiness through coordinated GitHub release, Zenodo archiving, and software-paper submission

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

This release marks a major project transition:

- MATLAB remains the **reference implementation** for validation and numerical behaviour
- Python is now a **working public implementation**, distributed on PyPI and usable through CLI entry points
- The release is linked to Zenodo for archival/citation purposes
- The associated JOSS paper has been submitted and is awaiting editorial triage

A remaining post-release task is to fully synchronize all documentation pages with the new repository status, because some website text still reflects the earlier “Python scaffold” stage.

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
