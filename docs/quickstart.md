# Quickstart

This section provides a minimal example to run PME-toolkit and verify that the installation works correctly.

PME-toolkit can be used in two ways:

- Option A — try a ready-to-run reference case (recommended)
- Option B — use PME-toolkit on your own data

---

## Python (recommended)

### Option A — Run the self-contained reference case

Clone the repository to access ready-to-run benchmark cases:

    git clone https://github.com/cnr-inm-mao/pme-toolkit.git
    cd pme-toolkit
    git switch --detach v1.3.0
    python -m pip install -e ./python

The tag selection above installs v1.3.0, including `auto`, `direct`, `snapshot`
and streaming. Other released versions are listed on the repository's Releases
page.

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

The solvers and streamed APIs require version 1.3.0 or later. Use
`pip install pme-toolkit==1.3.0` to select this release explicitly.
See [Input data](input_data.md) and
[Configuration](config_spec.md) for dataset and variable definitions.

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
- output files under `tests/cases/results/` for this reference configuration

The saved outputs include `report.mat` and a model file (`model.npz` in Python,
`model.mat` in MATLAB), together with diagnostic plots. Backmapping reads the
saved model from the preceding run.

## Solver choice

The reference case and benchmark inputs explicitly include:

```json
"solver": "auto"
```

This selects the smaller of the direct observation covariance and snapshot
Gram problems. Set `"direct"` or `"snapshot"` to select a particular solver.
Existing fit inputs that omit `solver` remain valid and default to `"auto"`
in both languages. No solver field is needed in a backmapping configuration.
See [Solver selection](snapshot.md#solver-selection) for the numerical contract.

---

## Notes

- the dataset under `tests/data/` is self-contained and requires no external downloads  
- JSON configuration files define the full workflow  
- ready-to-run examples are available in the repository under `tests/cases/`  
- for full benchmark workflows, see the *Benchmarks* and *Datasets* sections  
- the regular case runner loads the database into memory even when
  `solver="snapshot"`; use the [row-reader API](snapshot.md#streamed-observations-and-compact-native-models)
  for streamed observation data
