# PME-toolkit (Python)

Python implementation of **PME-toolkit** for **design-space dimensionality reduction** in parametric shape optimization.

Supports:

* **PME (Parametric Model Embedding)**
* **PI-PME (Physics-Informed PME)**
* **PD-PME (Physics-Driven PME)**
* analytical **backmapping** to original design variables

---

## Overview

The Python package provides a fully functional implementation of PME-based workflows using a **JSON-driven interface** for reproducible studies.

It is aligned with the MATLAB implementation and validated through **cross-language regression tests**.

---

## Installation

### From PyPI

This installs the latest published version:

```
pip install pme-toolkit
```

### From source (development mode)

Run from the repository root to install the checked-out source revision:

```
pip install -e python/
```

The solver and streaming APIs described below require version 1.3.0 or later.
To install this release explicitly, use `pip install pme-toolkit==1.3.0`.

---

## Command-line interface

Run a PME case:

```
pme-run tests/cases/test_glider.json
```

Run backmapping:

```
pme-back tests/cases/test_glider_back.json
```

The CLI:

* parses the JSON configuration
* executes the PME workflow
* writes outputs to the specified `outdir`
* uses the same case schema as MATLAB, with zero-based JSON indices

## Solver and output settings

Fitting cases accept:

```json
{"solver": "auto"}
```

`auto` selects the smaller of the direct observation covariance and snapshot
sample Gram problems. Use `direct` or `snapshot` to choose explicitly. Older
case files without `solver` remain valid and default to `auto`.

The runner writes `report.mat` and, when `io.save_model=true` (the default),
`model.npz`. Set the latter flag when a subsequent `pme-back` run needs a saved
model. `io.transpose_if` accepts `auto`, `never` and `always`; `auto` infers
orientation from the configured row layout. Relative paths are resolved
against the fitting JSON directory.

---

## Programmatic usage

Example:

```
from pme_toolkit.model import fit_from_case

model = fit_from_case("tests/cases/test_glider.json")

print(model.nconf)
print(model.alpha_train.shape)
```

`fit_from_case` fits existing local inputs and returns a model without writing
the report or plots. Use `pme_toolkit.run_case.run_case` for the complete case
workflow, including dataset retrieval when configured.

For observations read or generated in blocks, use `fit_streaming`,
`transform_streaming` and `backmap_streaming`. The regular runner keeps the
database in memory for every solver setting. See the
[Python API](https://cnr-inm-mao.github.io/pme-toolkit/python_api/) and
[snapshot formulation](https://cnr-inm-mao.github.io/pme-toolkit/snapshot/).

---

## Repository integration

The Python implementation is part of the full PME-toolkit repository:

* shared **JSON configuration format**
* shared **datasets**
* shared **benchmark definitions**
* validated against MATLAB through **regression testing**

---

## Testing

From repository root:

```
pytest tests/python -q
```

Test suite covers:

* configuration loading
* PME workflows
* backmapping
* regression against MATLAB reference
* direct/snapshot agreement, numerical rank and repeated eigenvalue clusters
* streamed fitting, independent query projection and native backmapping

---

## Datasets

* lightweight test dataset:

  tests/data/

* benchmark datasets:

  databases/

---

## Status

The Python implementation is **fully functional** for PME, PI-PME, and PD-PME within the current scope.

It is maintained alongside the MATLAB implementation. The shared fixtures and
complete airfoil regression specify the verified cross-language coverage.

