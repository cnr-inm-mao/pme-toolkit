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
- provides **analytical reconstruction of the original design variables**
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
- **direct and snapshot formulations** in MATLAB and Python, with automatic
  solver selection, diagonal weights and numerical-rank control
- **streamed observation readers**, compact native-variable models and
  cross-Gram projection for data larger than memory
- **cross-language regression testing** (MATLAB ↔ Python)  
- benchmark configurations for **glider**, **airfoil** and **propeller** cases
- [complete Zenodo airfoil regression](docs/zenodo-regression.md) and a
  [reproducible million-coordinate experiment](docs/reproducibility.md)

See [Snapshot formulation](docs/snapshot.md) for the equations, numerical
tolerances, model compatibility and memory limits in version 1.3.0.
Published packages are available through the PyPI badge.

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

Run these commands from the repository root after installing the Python package
or making MATLAB available. The bundled tiny case needs no dataset download.

### MATLAB

    matlab -batch "run_pme('tests/cases/test_glider.json')"

    matlab -batch "run_back('tests/cases/test_glider_back.json')"

---

### Python

    pme-run tests/cases/test_glider.json

    pme-back tests/cases/test_glider_back.json

### Solver configuration

The same fitting JSON is used by MATLAB and Python. Distributed examples and
benchmarks explicitly set:

```json
{"solver": "auto"}
```

`auto` chooses between the direct observation covariance and the snapshot
sample Gram matrix. Select `direct` or `snapshot` explicitly for a matched
comparison. Existing inputs without `solver` also default to `auto`; no input
migration is required. This option belongs to the fitting case, not the
backmapping JSON. See the [configuration specification](docs/config_spec.md).

---

## MATLAB–Python consistency

PME-toolkit includes shared MATLAB/Python fixtures, a reference glider case,
and a [complete Zenodo airfoil regression](docs/zenodo-regression.md) covering
PME, PI-PME and PD-PME with all three solver settings.

The regression validates:

- retained dimensionality (`nconf`)  
- eigenvalues of the reduced system  
- reduced modes (up to sign ambiguity)  

---

## Benchmarks and datasets

Benchmark definitions are available for:

- `glider`
- `airfoil`
- `propeller` (standard PME)

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

Install the latest published package from PyPI:

    pip install pme-toolkit

To use the source revision checked out in this repository:

    pip install -e ./python

The direct/snapshot solver setting and streamed APIs described here require
version 1.3.0 or later. To install this release explicitly:

    pip install pme-toolkit==1.3.0

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

- MATLAB and Python implement PME, PI-PME and PD-PME, direct and snapshot
  fitting, and the advanced streamed APIs.
- Cross-language checks cover the shared fixtures and the cases documented
  in [Reproducibility](docs/reproducibility.md).
- The standard case runners load the database into memory. Large observation
  sets use the reader-based API described in [Snapshot formulation](docs/snapshot.md).

---

## Citation

See:

    CITATION.cff

---

## License

MIT License
