# Python implementation

This folder contains the **Python implementation** of PME-toolkit.

## Scope

The Python package supports the repository workflow for:

- **PME**
- **PI-PME**
- **PD-PME**
- analytical **backmapping** to the original parametric variables

within the current **shape-optimization** scope of the project.

The implementation is fully integrated in the **JSON-driven workflow** used across the repository.

---

## Role within PME-toolkit

PME-toolkit provides a **dual MATLAB/Python implementation**.

The Python code:

- supports the same **methods (PME, PI-PME, PD-PME)** as MATLAB  
- uses the same **JSON configuration format**  
- is validated against MATLAB through **cross-language regression tests**  
- provides a command-line interface for reproducible execution  

---

## Installation

From the repository root:

    pip install -e python/

This installs the package in editable mode and exposes the CLI entry points.

---

## Command-line interface

The Python implementation provides CLI tools aligned with the repository workflow.

Run a PME case:

    pme-run tests/cases/test_glider.json

Run backmapping:

    pme-back tests/cases/test_glider_back.json

These commands:

- parse the JSON configuration  
- run the full PME workflow  
- write outputs to the specified `outdir`  
- ensure compatibility with MATLAB-generated results  

---

## Programmatic usage

Example:

    from pme_toolkit.model import fit_from_case

    model = fit_from_case("tests/cases/test_glider.json")

    print(model.nconf)
    print(model.alpha_train.shape)

---

## Outputs

Running a PME case generates:

- model data (Python structures and/or saved files)
- reduced coordinates
- quantities needed for backmapping
- outputs written to the `outdir` specified in the JSON case

---

## Testing

From the repository root:

    pytest tests/python -q

The test suite includes:

- configuration loading
- PME execution
- backmapping
- regression tests against MATLAB reference results

---

## Datasets

The Python implementation uses the same datasets as the MATLAB side.

- lightweight test dataset:

    tests/data/

- benchmark datasets:

    databases/

---

## Status

The Python implementation is **fully functional** for PME, PI-PME, and PD-PME within the current repository scope.

It is actively maintained in alignment with the MATLAB implementation and validated through cross-language regression tests.
