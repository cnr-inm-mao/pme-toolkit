# Benchmarks

This directory contains the **benchmark definitions** used to run PME-toolkit workflows for:

- **PME**
- **PI-PME**
- **PD-PME**

on the supported shape-optimization datasets.

Benchmarks are defined through **JSON configuration files** and are compatible with both **MATLAB and Python implementations**.

---

## Structure

Benchmarks are organized by:

1. **dataset-selection strategy**
2. **method family**

    benchmarks/
    ├── standard/
    │   ├── pme/
    │   ├── pi_pme/
    │   └── pd_pme/
    └── goal_oriented/
        ├── pi_pme/
        └── pd_pme/

Each leaf folder corresponds to a specific **benchmark case** and typically contains:

- one or more `case.json` files  
- optional `backmapping.json` configurations  
- a local `README.md` describing the case  

---

## Supported datasets

The current repository includes benchmark configurations for:

- `glider`
- `airfoil`

These datasets are described under:

- `databases/glider/`
- `databases/airfoil/`

---

## Workflow

Each benchmark defines a **fully reproducible workflow** based on JSON configuration files.

A typical workflow consists of:

1. running PME / PI-PME / PD-PME:

       pme-run <case.json>

   or

       matlab -batch "run_pme('<case.json>')"

2. optionally running backmapping:

       pme-back <backmapping.json>

   or

       matlab -batch "run_back('<backmapping.json>')"

Outputs are written to the `outdir` specified in the JSON configuration.

---

## Dataset availability

Benchmark folders define **configuration and workflow**, while datasets may be:

- bundled (for testing purposes), or  
- referenced externally via metadata in `databases/`  

---

## Recommended starting point

For a fully reproducible and self-contained run, use:

    tests/cases/test_glider.json

This case relies on a lightweight dataset included in:

    tests/data/

---

## Notes

- Benchmarks are designed to be **implementation-independent**  
- The same JSON files can be executed with both MATLAB and Python  
- Cross-language consistency is ensured through regression testing on reference cases  
