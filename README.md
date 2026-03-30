<p align="center">
  <a href="https://cnr-inm-mao.github.io/pme-toolkit/">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="docs/assets/logos/logo-hori-nobg.png">
      <source media="(prefers-color-scheme: light)" srcset="docs/assets/logos/logo-hori.png">
      <img src="docs/assets/logos/logo-hori.png" width="300">
    </picture>
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

---

## Overview

**PME-toolkit** is an open-source framework for **design-space dimensionality reduction in parametric shape optimization**, based on **Parametric Model Embedding (PME)** and its physics-aware extensions (**PI-PME**, **PD-PME**).

Unlike standard dimensionality reduction techniques (e.g. PCA/POD), PME:

- preserves a **direct analytical link to the original design variables**
- enables **exact backmapping to the parametric model**
- supports **weighted and physics-aware embeddings**

This makes PME particularly suited for **CAD-based engineering design workflows**, where interpretability and parametric consistency are essential.

The toolkit provides a **reproducible, benchmark-driven workflow** with dual **Python/MATLAB implementations**, enabling consistent analysis, validation, and integration within simulation-based design optimization pipelines.

---

## 📌 Relationship with the original PME implementation

The original MATLAB proof-of-concept implementation associated with the CMAME paper is available here:

👉 https://github.com/cnr-inm-mao/PME  

That repository is maintained as a **legacy reference for reproducibility**, while **PME-toolkit is the current and actively developed framework**.

---

## Statement of need

Simulation-Based Design Optimization (SBDO) is often limited by the **curse of dimensionality** associated with high-dimensional parametric design spaces.

Classical dimensionality reduction techniques:

- rely on geometric variance only  
- do not preserve the parametric structure  
- do not allow direct reconstruction of design variables  

PME addresses these limitations by constructing a **low-dimensional embedding of the design space** that:

- preserves a direct link to original design variables  
- enables **analytical backmapping**  
- supports **efficient optimization in reduced coordinates**  
- maintains **physical interpretability of the solution space**

---

## Key features

- dual **Python / MATLAB** implementation  
- support for **PME, PI-PME, and PD-PME**  
- **JSON-driven workflows** for reproducibility  
- **analytical backmapping** to original variables  
- **weighted and physics-aware embeddings**  
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

    matlab -batch "run_pme('tests/cases/test_glider.json')"

    matlab -batch "run_back('tests/cases/test_glider_back.json')"

---

### Python

    pme-run tests/cases/test_glider.json

    pme-back tests/cases/test_glider_back.json

---

## MATLAB–Python consistency

PME-toolkit includes a **cross-language regression test** on a reference glider case.

The regression validates:

- retained dimensionality (`nconf`)  
- eigenvalues of the reduced system  
- reduced modes (up to sign ambiguity)  

---

## Benchmarks and datasets

Benchmark definitions are available for:

- `glider`
- `airfoil`

Lightweight datasets:

    tests/data/

Larger datasets are managed via:

    databases/

---

## Documentation

https://cnr-inm-mao.github.io/pme-toolkit/

    mkdocs serve

---

## Installation

### Python

    pip install pme-toolkit

    pip install -e python/

### MATLAB

    addpath(genpath('matlab/src'))

---

## Testing

### MATLAB

    matlab -batch "cd('tests/matlab'); run_tests"

### Python

    pytest tests/python -q

---

## Status

PME-toolkit is an **actively developed research software package**.

- Python: fully functional and recommended  
- MATLAB: reference implementation for validation  
- cross-language consistency ensured  

---

## Citation

See:

    CITATION.cff

---

## License

MIT License
