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
If this setting is omitted, fitting uses `auto`. The regular model and all
downstream APIs are shared by the two solvers. JSON and Python configuration
indices are zero-based; `baseline_col=0` selects the first input sample.

The positive `baseline_col` values previously accepted through a MATLAB-style
interpretation now follow this same zero-based convention. Custom Python
configurations that used one-based indices must subtract one. Existing
distributed examples use `baseline_col=0` and keep their baseline.

## Case outputs

`run_case` returns a dictionary with `cfg`, `layout`, `meta`, `case_json`, `DB`,
`DB_used`, `model`, `report`, `outdir`, `saved`, `filter_info` and `filter_mask`.
The report is saved as `report.mat`. With `io.save_model=true` (the default),
model saving writes `model.npz` and records its path under `saved.model_npz`.
With `false`, that saved-file entry is absent and the in-memory `model` remains
available. An omitted `io.outdir` uses `results` under the fitting case directory.
`PmeModel.load` restores that model for transformation or backmapping.

The effective solver and its diagnostics are available through
`result["model"].stats_w["snapshot"]`, including `solver_requested`, `solver`,
`matrix_dimension`, `numerical_rank` and `achieved_ci`. The `snapshot`
diagnostic name applies to both solvers.

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
The compact streaming model is distinct from `PmeModel`. The standard
`run_case` workflow retains its database in memory for every solver choice.

---

## Status

- published package versions are installable via PyPI; the direct/snapshot
  solvers and streamed APIs require version 1.3.0 or later
- validated against MATLAB reference through regression tests
- recommended for standard usage

MATLAB remains the reference for numerical validation.
