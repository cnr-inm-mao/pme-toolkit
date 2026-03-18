# Quickstart

This section provides a minimal example to run PME-toolkit and verify that the installation works correctly.

PME-toolkit can be used in two ways:

- Option A — try a ready-to-run reference case (recommended)
- Option B — use PME-toolkit on your own data

---

## Python (recommended)

### Option A — Try PME-toolkit in 2 minutes

Clone the repository to access ready-to-run benchmark cases:

    git clone https://github.com/cnr-inm-mao/pme-toolkit.git
    cd pme-toolkit
    pip install -e .

Run a reference case:

    pme-run tests/cases/test_glider.json

Run backmapping:

    pme-back tests/cases/test_glider_back.json

---

### Option B — Use PME-toolkit on your own data

Install from PyPI:

    pip install pme-toolkit

Run PME with your configuration file:

    pme-run your_config.json

Run backmapping:

    pme-back your_backmapping_config.json

See the *Input Format* section for details on how to define datasets and variables.

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
- ready-to-run examples are available in the repository under `tests/cases/`  
- for full benchmark workflows, see the *Benchmarks* and *Datasets* sections  
