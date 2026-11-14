# Python API

The Python package provides a **working implementation of PME-toolkit**, aligned with the MATLAB reference workflow.

## Main entry points

### CLI

    pme-run <case.json>
    pme-back <case_back.json>

### Python usage

    from pme_toolkit.run_case import run_case
    from pme_toolkit.run_back import run_back

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
- direct and snapshot symmetric eigensolvers with automatic selection,
  vector weights and numerical-rank diagnostics
- streamed fitting, compact native backmapping and cross-Gram query encoding

The low-level `snapshot_decompose(pc, weights, options=None)` accepts centered
data with samples in columns and returns resolved eigenvalues, complete modes,
training coordinates, sample eigenvectors and diagnostics. See
[Snapshot formulation](snapshot.md) for conventions and migration of custom
code using stored weights. `direct_decompose(pc, weights, options=None)` has
the same outputs; `decompose(pc, weights, options=None, solver="auto")` selects
the smaller symmetric problem. Regular fits accept the same choice in
`cfg["solver"]`.

## Row-reader workflow

```python
from pme_toolkit import fit_streaming, transform_streaming, backmap_streaming

model = fit_streaming(reader, (Q, S), weights, native,
                      {"block_rows": 2048}, ci=0.95)
coordinates = transform_streaming(model, reader, query_reader, T, weights)
native_predictions = backmap_streaming(model, coordinates)
```

Readers return raw observation rows using zero-based, half-open bounds
`reader(start, stop)`. The metric is a fixed vector or row reader. `native`
has shape `(M, S)` in the already prepared coordinate system chosen by the
caller. Query coordinates are `(T, N)` and native predictions are `(M, T)`.
An optional `mode_writer(start, stop, modes)` receives observation modes in
a second pass. See [Snapshot formulation](snapshot.md) for a complete example,
provider responsibilities, and storage requirements.

---

## Status

- fully functional and installable via PyPI
- validated against MATLAB reference through regression tests
- recommended for standard usage

MATLAB remains the reference for numerical validation.
