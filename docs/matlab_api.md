# MATLAB API

The MATLAB implementation provides a reference interface for PME-toolkit workflows.

---

## Setup

Add the source folder to the MATLAB path:

    addpath(genpath("matlab/src"));

---

## Running a case

A dimensionality reduction workflow can be executed from a JSON configuration file:

    out = pme.run_case("tests/cases/test_glider.json");

---

## Backmapping

Backmapping can be performed using a dedicated configuration:

    out = pme.backmapping("tests/cases/test_glider_back.json");

---

## Output

The returned structure `out` typically includes:

- reduced coordinates  
- variance information  
- reconstruction metrics  
- model data  

Exact contents depend on the configuration.

---

## Wrappers

Repository-level wrappers are available:

- `run_pme.m`
- `run_back.m`

These provide a simplified interface to the same JSON-driven workflow:

    run_pme("tests/cases/test_glider.json")
    run_back("tests/cases/test_glider_back.json")

---

## Notes

- MATLAB and Python implementations follow the same configuration structure  
- JSON files define the full workflow  
- MATLAB is useful for validation and comparison with the reference implementation  
