# Python API

The Python package provides a **working implementation of PME-toolkit**, aligned with the MATLAB reference workflow.

## Main entry points

### CLI

    pme-run <case.json>
    pme-back <case_back.json>

### Python usage

    from pme_toolkit import run_case, run_back

    run_case("tests/cases/test_glider.json")
    run_back("tests/cases/test_glider_back.json")

---

## Scope

The Python implementation supports:

- PME, PI-PME, PD-PME model construction
- JSON-driven workflows
- dimensionality reduction and variance analysis
- backmapping to original variables
- model persistence (`model.npz`)
- snapshot Gram eigensolver with vector weights and numerical-rank diagnostics

The low-level `snapshot_decompose(pc, weights, options=None)` accepts centered
data with samples in columns and returns resolved eigenvalues, complete modes,
training coordinates, sample eigenvectors and diagnostics. See
[Snapshot formulation](snapshot.md) for conventions and migration of custom
code using stored weights.

---

## Status

- fully functional and installable via PyPI
- validated against MATLAB reference through regression tests
- recommended for standard usage

MATLAB remains the reference for numerical validation.
