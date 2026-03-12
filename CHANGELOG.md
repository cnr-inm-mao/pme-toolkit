# Changelog

All notable changes to **PME-toolkit** will be documented in this file.

The format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and semantic versioning principles.

---

## [1.0.1] – Initial public release

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

---

## Planned for future releases

- Full Python implementation of PME workflow
- Additional benchmark datasets
- Extended dataset packaging and download automation
- Continuous integration
- Additional validation tests
