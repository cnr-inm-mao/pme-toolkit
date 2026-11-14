# Benchmarks

The repository provides **benchmark cases for dimensionality reduction workflows** based on PME and its variants.

Each benchmark is defined by a configuration file and an associated versioned
dataset. The [reproducibility protocols](reproducibility.md) identify the cases
covered by automated numerical comparisons.

---

## Available benchmarks

- `glider`
- `airfoil`
- `propeller` (standard PME)

Benchmarks are organized under `benchmarks/` by:

- method family (PME, PI-PME, PD-PME)
- selection strategy (standard, goal-oriented)

| Case family | Glider | Airfoil | Propeller |
|---|---|---|---|
| Standard PME | Available | Available | Available |
| Standard PI-PME / PD-PME | Available | Available | — |
| Goal-oriented PI-PME / PD-PME | Available | Available | — |

---

## Running a benchmark

Benchmarks are executed using the standard workflow via a JSON configuration file.
The distributed cases explicitly set `"solver": "auto"`. Changing it to
`"direct"` or `"snapshot"` selects the numerical formulation while preserving
the case data, source metric, preprocessing and output workflow. For a solver
comparison, keep all other configuration entries unchanged. Cases that omit
the field remain valid and use `auto`.

### Python

    pme-run benchmarks/standard/pme/glider/case.json

### MATLAB

    run_pme("benchmarks/standard/pme/glider/case.json")

Running a benchmark produces:

- reduced coordinates  
- variance analysis  
- reconstruction error metrics  
- visualization outputs  
- trained model  

---

## Benchmark structure

Each benchmark includes:

- a configuration file (`case.json`)
- references to dataset files
- method and preprocessing settings
- output definitions

The configuration file fully defines the experiment.

---

## Data dependencies

Benchmarks rely on datasets that may be:

- included in lightweight form (`tests/data/`)
- referenced through metadata (`databases/`)
- distributed externally (e.g. Zenodo)

The standard runner downloads and extracts a missing benchmark database when
the matching `databases/<name>/dataset.json` metadata is available. Manual
download remains possible; supply the corresponding local paths in the case
configuration. Relative paths are resolved from the case directory.

---

## Current maturity

- **airfoil** → pinned dataset record [10.5281/zenodo.18958555](https://doi.org/10.5281/zenodo.18958555);
  complete PME/PI/PD regression against the preceding solver and across MATLAB
  and Python is specified in [Zenodo regression](zenodo-regression.md).
- **glider** → pinned dataset record [10.5281/zenodo.18936594](https://doi.org/10.5281/zenodo.18936594);
  a tiny local fixture and a full Python case workflow are included in testing.
- **propeller** → pinned dataset record [10.5281/zenodo.20207996](https://doi.org/10.5281/zenodo.20207996);
  a standard PME configuration is provided. This does not imply that the full
  propeller dataset has the same regression coverage as airfoil.

---

## Role of benchmarks

Benchmarks provide:

- validation of dimensionality reduction workflows  
- comparison between PME, PI-PME, and PD-PME  
- reproducible test cases for development and research  

They form the basis for systematic evaluation and benchmarking of methods.
