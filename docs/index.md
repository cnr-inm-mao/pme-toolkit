<p align="left">
  <a href="https://cnr-inm-mao.github.io/pme-toolkit">
    <img src="assets/logos/logo-hori-nobg.png" width="300">
  </a>
</p>

# PME-toolkit

PME-toolkit is an open-source framework for **design-space dimensionality reduction in parametric shape optimization** based on **Parametric Model Embedding (PME)** and its physics-aware extensions (**PI-PME**, **PD-PME**).

It provides a **reproducible, benchmark-driven workflow** with dual **Python/MATLAB implementations**, enabling consistent analysis, validation, and integration within simulation-based design optimization pipelines.

---

## What is in the repository

- a MATLAB reference implementation;
- a **fully functional Python package (available on PyPI)**;
- benchmark definitions;
- dataset metadata;
- local tests;
- a JOSS software paper submission.

---

## Installation

### Python

    pip install pme-toolkit

### MATLAB

    addpath(genpath("matlab/src"));

---

## Quick example

### Python

    pme-run tests/cases/test_glider.json
    pme-back tests/cases/test_glider_back.json

### MATLAB

    run_pme("tests/cases/test_glider.json")
    run_back("tests/cases/test_glider_back.json")

---

## Current status

PME-toolkit v1.2 is a **public released package**:

- available on PyPI
- archived on Zenodo
- submitted to JOSS

- Python implementation: fully functional and recommended for use  
- MATLAB implementation: maintained as reference for validation  

---

Use the navigation menu to access detailed documentation on configuration, APIs, benchmarks, datasets, reproducibility, and backmapping.
