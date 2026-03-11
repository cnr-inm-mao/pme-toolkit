# PME-toolkit

[![Docs](https://img.shields.io/badge/docs-online-blue)](https://cnr-inm-mao.github.io/pme-toolkit/)

[![Tests](https://github.com/cnr-inm-mao/pme-toolkit/actions/workflows/python-ci.yml/badge.svg)](https://github.com/cnr-inm-mao/pme-toolkit/actions/workflows/python-ci.yml)

[![DOI](https://zenodo.org/badge/XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)

PME-toolkit is an open-source repository for **design-space dimensionality reduction in parametric shape optimization** based on **Parametric Model Embedding (PME)** and its physics-aware variants.

The repository currently contains:

- a **MATLAB reference implementation** of **PME**, **PI-PME**, and **PD-PME** for shape-optimization workflows;
- a **Python scaffold** for shared configuration handling and future porting;
- **benchmark case definitions** under `benchmarks/`;
- **dataset metadata and download support** under `databases/` for the **glider** and **airfoil** benchmarks;
- **tests** with a small bundled glider dataset under `tests/`;
- a **MkDocs documentation site** under `docs/`.

## Current status

At the current repository stage:

- **MATLAB is the reference implementation**;
- **PME, PI-PME, and PD-PME are implemented in MATLAB** for the current shape-optimization scope;
- the **Python package is not yet feature-complete** and should be considered infrastructure for the future port;
- the most reliable self-contained workflow is the **test glider case** in `tests/`;
- the full benchmark workflows may require **external datasets** not bundled directly in the repository.

## Methods in scope

### PME

PME builds an augmented representation of the design space by combining:

- geometric deviations from a baseline configuration;
- original design variables.

The resulting reduced basis supports **analytical backmapping** to the original parametric variables.

### PI-PME

PI-PME extends PME by including **physical observables** such as distributed fields and/or scalar performance indicators.

### PD-PME

PD-PME is the physics-driven variant currently used in the repository for **shape optimization**. In this scope it is implemented in MATLAB and can be run through the same JSON-driven workflow. Broader generalization beyond shape optimization remains future work.

## Repository layout

```text
pme-toolkit/
├── README.md
├── LICENSE
├── CITATION.cff
├── mkdocs.yml
├── run_pme.m
├── run_back.m
├── matlab/
├── python/
├── benchmarks/
├── databases/
├── docs/
├── tests/
└── paper/
```

## Quick start

### MATLAB: self-contained local test case

The repository includes a tiny glider dataset under `tests/data/` that can be used without external downloads.

```matlab
addpath(genpath("matlab/src"));
out = pme.run_case("tests/cases/test_glider.json");
```

For standalone backmapping:

```matlab
addpath(genpath("matlab/src"));
out = pme.backmapping("tests/cases/test_glider_back.json", "x01", [0.1; 0.7; 0.3; 0.9; 0.2]);
```

### MATLAB: benchmark runner wrappers

Two thin wrappers are provided at repository root:

- `run_pme.m`
- `run_back.m`

They mirror the JSON-driven workflow used in the benchmark folders.

Example:

```matlab
run_pme("benchmarks/standard/pme/glider/case.json");
run_back("benchmarks/standard/pme/glider/backmapping.json");
```

## Benchmarks and datasets

The repository contains benchmark definitions for:

- `glider`
- `airfoil`

At this stage:

- **glider** is the best documented benchmark and includes dataset metadata in `databases/glider/`;
- **airfoil** also includes dataset metadata in `databases/airfoil/`;

See:

- `benchmarks/README.md`
- `databases/README.md`
- `docs/benchmarks.md`
- `docs/datasets.md`

## MATLAB and Python subpackages

- `matlab/README.md` describes the current reference implementation.
- `python/README.md` describes the current Python status and limitations.

## Documentation

The documentation site is built with **MkDocs**.

Main pages include:

- overview
- quickstart
- configuration specification
- MATLAB API
- Python API
- reproducibility notes
- citation
- backmapping
- benchmarks
- datasets

Build locally with:

```bash
mkdocs serve
```

## Testing

### MATLAB

Run the MATLAB regression suite from repository root:

```matlab
run("tests/run_tests.m")
```

### Python

From `python/`:

```bash
PYTHONPATH=src pytest -q
```

The Python tests currently validate the configuration loader scaffold only.

## Citation

If you use PME-toolkit, cite the software repository together with the methodological publications listed in `CITATION.cff` and `paper/paper.md`.

## License

This repository is released under the MIT License.
