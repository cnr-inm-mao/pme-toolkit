# Quickstart

This section provides a minimal example to run PME-toolkit and verify that the installation works correctly.

---

## Python (recommended)

Install from PyPI:

    pip install pme-toolkit

Run a reference case:

    pme-run tests/cases/test_glider.json

Run backmapping:

    pme-back tests/cases/test_glider_back.json

---

## MATLAB

Add the source folder to the path:

    addpath(genpath("matlab/src"));

Run a reference case:

    run_pme("tests/cases/test_glider.json")

Run backmapping:

    run_back("tests/cases/test_glider_back.json")

---

## What happens

Running the example produces:

- reduced coordinates  
- variance and mode information  
- reconstruction error metrics  
- output files in the `results/` directory  

---

## Notes

- the dataset under `tests/data/` is self-contained and requires no external downloads  
- JSON configuration files define the full workflow  
- for full benchmark workflows, see the *Benchmarks* and *Datasets* sections  
