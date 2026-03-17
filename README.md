<p align="center">
  <a href="https://cnr-inm-mao.github.io/pme-toolkit/">
    <img src="docs/assets/logos/logo-hori.png" width="300">
  </a>
</p>

# PME-toolkit

[![Docs](https://img.shields.io/badge/docs-online-blue)](https://cnr-inm-mao.github.io/pme-toolkit/)
[![Docs build](https://github.com/cnr-inm-mao/pme-toolkit/actions/workflows/docs-pages.yml/badge.svg)](https://github.com/cnr-inm-mao/pme-toolkit/actions/workflows/docs-pages.yml)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18962859.svg)](https://doi.org/10.5281/zenodo.18962859)
[![PyPI](https://img.shields.io/pypi/v/pme-toolkit?logo=pypi&logoColor=white)](https://pypi.org/project/pme-toolkit/)
[![Python](https://img.shields.io/pypi/pyversions/pme-toolkit?logo=python&logoColor=white)](https://pypi.org/project/pme-toolkit/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![MATLAB tests](https://github.com/cnr-inm-mao/pme-toolkit/actions/workflows/matlab-tests.yml/badge.svg)](https://github.com/cnr-inm-mao/pme-toolkit/actions/workflows/matlab-tests.yml)
[![Python tests](https://github.com/cnr-inm-mao/pme-toolkit/actions/workflows/python-tests.yml/badge.svg)](https://github.com/cnr-inm-mao/pme-toolkit/actions/workflows/python-tests.yml)

PME-toolkit is an open-source framework for **design-space dimensionality reduction in parametric shape optimization** based on **Parametric Model Embedding (PME)** and its physics-aware extensions (**PI-PME**, **PD-PME**).

It provides a **reproducible, benchmark-driven workflow** with dual **Python/MATLAB implementations**, enabling consistent analysis, validation, and integration within simulation-based design optimization pipelines.

---

## Statement of need

Simulation-Based Design Optimization (SBDO) is often limited by the **curse of dimensionality** associated with high-dimensional parametric design spaces.

PME-toolkit addresses this limitation by constructing a **low-dimensional embedding of the design space** that:

- preserves a direct link to original design variables  
- enables **analytical backmapping**  
- supports **efficient optimization in reduced coordinates**  
- maintains **physical interpretability of the solution space**

This makes PME particularly suited for **parametric CAD-based shape optimization workflows** in marine and aerospace engineering.

---

## Key features

- dual **Python / MATLAB** implementation  
- support for **PME, PI-PME, and PD-PME**  
- **JSON-driven workflows** for reproducibility  
- **analytical backmapping** to original variables  
- **cross-language regression testing** (MATLAB ↔ Python)  
- benchmark-ready structure for **glider** and **airfoil** cases  

---

## Repository structure

Core components:

    pme-toolkit/
    ├── run_pme.m        # MATLAB entry point
    ├── run_back.m       # MATLAB backmapping
    ├── matlab/          # MATLAB implementation
    ├── python/          # Python package
    ├── benchmarks/      # JSON benchmark definitions
    ├── databases/       # dataset metadata
    ├── tests/           # MATLAB/Python tests
    ├── docs/            # documentation (MkDocs)
    └── paper/           # JOSS paper draft

---

## Quick start

### MATLAB

Run a reference case:

    matlab -batch "run_pme('tests/cases/test_glider.json')"

Run backmapping:

    matlab -batch "run_back('tests/cases/test_glider_back.json')"

---

### Python

Run PME:

    pme-run tests/cases/test_glider.json

Run backmapping:

    pme-back tests/cases/test_glider_back.json

---

## MATLAB–Python consistency

PME-toolkit includes a **cross-language regression test** on a reference glider case.

The regression validates consistency between MATLAB and Python implementations in terms of:

- retained dimensionality (`nconf`)  
- eigenvalues of the reduced system  
- reduced modes (up to sign ambiguity)  

This ensures reproducibility and numerical alignment across implementations.

---

## Benchmarks and datasets

Benchmark definitions are available for:

- `glider`
- `airfoil`

A lightweight dataset is bundled under:

    tests/data/

Larger datasets are described in:

- `databases/`
- documentation pages

---

## Documentation

Full documentation is available at:

https://cnr-inm-mao.github.io/pme-toolkit/

Build locally with:

    mkdocs serve

---

## Testing

### MATLAB

    matlab -batch "cd('tests/matlab'); run_tests"

### Python

    pytest tests/python -q

---

## Installation

### Python

Install from PyPI:

    pip install pme-toolkit

For development (editable install from repository):

    pip install -e python/

### MATLAB

No installation required.

Add the repository root (or `matlab/src`) to your MATLAB path, e.g.:

    addpath(genpath('matlab/src'))

---

## Status

PME-toolkit is actively developed and maintained.

- Python implementation: fully functional and recommended for use  
- MATLAB implementation: maintained for validation and benchmarking  
- Cross-language consistency ensured via regression tests  

---

## Citation

If you use PME-toolkit, please cite the software release and the associated methodological publications listed in:

    CITATION.cff

---

## License

This project is distributed under the MIT License.
