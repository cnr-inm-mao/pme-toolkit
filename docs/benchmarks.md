# Benchmarks

The repository provides **benchmark cases for dimensionality reduction workflows** based on PME and its variants.

Each benchmark is a **fully reproducible experiment**, defined by a configuration file and associated data.

---

## Available benchmarks

- `glider`
- `airfoil`

Benchmarks are organized under `benchmarks/` by:

- method family (PME, PI-PME, PD-PME)
- selection strategy (standard, goal-oriented)

---

## Running a benchmark

Benchmarks are executed using the standard workflow via a JSON configuration file.

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

Users may need to download datasets and update paths accordingly.

---

## Current maturity

- **airfoil** → benchmark definitions and dataset metadata available on Zenodo (DOI: [10.5281/zenodo.18958554](https://doi.org/10.5281/zenodo.18958554))
- **glider** → benchmark definitions and dataset metadata available on Zenodo (DOI: [10.5281/zenodo.18936593](https://doi.org/10.5281/zenodo.18936593))

---

## Role of benchmarks

Benchmarks provide:

- validation of dimensionality reduction workflows  
- comparison between PME, PI-PME, and PD-PME  
- reproducible test cases for development and research  

They form the basis for systematic evaluation and benchmarking of methods.
