<p align="center">
  <a href="https://cnr-inm-mao.github.io/pme-toolkit/">
    <img src="docs/assets/logos/logo-hori.png" width="300">
  </a>
</p>

# PME-toolkit

[![Docs](https://img.shields.io/badge/docs-online-blue)](https://cnr-inm-mao.github.io/pme-toolkit/)
[![Docs build](https://github.com/cnr-inm-mao/pme-toolkit/actions/workflows/docs-pages.yml/badge.svg)](https://github.com/cnr-inm-mao/pme-toolkit/actions/workflows/docs-pages.yml)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18962859.svg)](https://doi.org/10.5281/zenodo.18962859)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![MATLAB tests](https://github.com/cnr-inm-mao/pme-toolkit/actions/workflows/matlab-tests.yml/badge.svg)](https://github.com/cnr-inm-mao/pme-toolkit/actions/workflows/matlab-tests.yml)
[![Python tests](https://github.com/cnr-inm-mao/pme-toolkit/actions/workflows/python-tests.yml/badge.svg)](https://github.com/cnr-inm-mao/pme-toolkit/actions/workflows/python-tests.yml)

PME-toolkit implements **Parametric Model Embedding (PME)** and its physics-aware extensions (**PI-PME**, **PD-PME**) for **design-space dimensionality reduction in simulation-based shape optimization**.

The toolkit provides a **dual MATLAB/Python implementation**, supporting **JSON-driven reproducible workflows**, **analytical backmapping**, and **cross-language regression testing**.

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

- dual **MATLAB / Python** implementation  
- support for **PME, PI-PME, and PD-PME**  
- **JSON-driven workflows** for reproducibility  
- **analytical backmapping** to original variables  
- **cross-language regression testing** (MATLAB ↔ Python)  
- benchmark-ready structure for **glider** and **airfoil** cases  

---

## Repository structure

    pme-toolkit/
    ├── run_pme.m
    ├── run_back.m
    ├── matlab/
    ├── python/
    ├── benchmarks/
    ├── databases/
    ├── tests/
    ├── docs/
    └── paper/

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

Install locally:

    pip install -e python/

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

Local installation:

    pip install -e python/

PyPI (planned):

    pip install pme-toolkit

### MATLAB

No installation required.

---

## Citation

If you use PME-toolkit, please cite the software release and the associated methodological publications listed in:

    CITATION.cff

---

## License

This project is distributed under the MIT License.
