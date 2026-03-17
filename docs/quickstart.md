# Quickstart

## Python (recommended)

Install from PyPI:

    pip install pme-toolkit

Run PME on the reference case:

    pme-run tests/cases/test_glider.json

Run backmapping:

    pme-back tests/cases/test_glider_back.json

---

## MATLAB (reference implementation)

    addpath(genpath("matlab/src"));
    out = pme.run_case("tests/cases/test_glider.json");

Backmapping:

    out = pme.backmapping("tests/cases/test_glider_back.json", "x01", [0.1; 0.7; 0.3; 0.9; 0.2]);

---

## Notes

The tiny glider dataset under `tests/data/` provides a fully self-contained example for validation.

For full benchmark workflows, see the Benchmarks and Datasets sections.
