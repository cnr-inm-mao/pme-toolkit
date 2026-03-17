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

```
pip install pme-toolkit
```

### From source (development mode)

```
pip install -e python/
```

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
* ensures consistency with MATLAB results

---

## Programmatic usage

Example:

```
from pme_toolkit.model import fit_from_case

model = fit_from_case("tests/cases/test_glider.json")

print(model.nconf)
print(model.alpha_train.shape)
```

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

---

## Datasets

* lightweight test dataset:

  tests/data/

* benchmark datasets:

  databases/

---

## Status

The Python implementation is **fully functional** for PME, PI-PME, and PD-PME within the current scope.

It is actively maintained and serves as a **production-ready interface** for reproducible PME workflows.

