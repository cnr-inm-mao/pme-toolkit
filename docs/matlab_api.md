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

`pme.run_case` returns configuration, layout, dataset metadata, original and
filtered data, the fitted model, output directory, saved-file paths and report
(`out.cfg`, `out.layout`, `out.meta`, `out.DB`, `out.DB_used`, `out.model`,
`out.outdir`, `out.saved`, `out.rep`). Model saving writes `model.mat`; reporting
writes `report.mat` and figures.

For solver diagnostics, inspect `out.model.statsW.snapshot`, including
`solver_requested`, `solver`, `matrix_dimension`, `numerical_rank` and
`achieved_ci`. The `snapshot` diagnostic name is shared by both solvers.

`pme.backmapping` returns `out.x01`, physical reduced coordinates `out.alpha`,
the reconstructed augmented vector `out.P`, active variables `out.Uact`, the
requested output vector `out.U` and `out.written_files`.

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

`pme.snapshot_decompose(Pc, w, options)` exposes the snapshot solver for
already centered data with samples in columns. Its result contains resolved
eigenvalues, complete modes, training coordinates, sample eigenvectors and
diagnostics. `pme.weights_diag` builds vector weights for the normal fitting
path. `pme.direct_decompose(Pc, w, options)` exposes the equivalent symmetric
observation covariance solver. `pme.decompose(Pc, w, options, solver)` accepts
`'auto'`, `'direct'`, or `'snapshot'`; regular fitting uses `cfg.solver` with
default `'auto'`. See [Snapshot formulation](snapshot.md) for numerical options and
compatibility with legacy models.
An omitted `solver` field remains valid. JSON indices are zero-based and are
converted when reading the case; configurations assembled directly in MATLAB
use MATLAB's one-based indices.

## Row-reader workflow

```matlab
model = pme.fit_streaming(reader, [Q,S], weights, native, ...
    struct('block_rows',2048), 0.95);
coordinates = pme.transform_streaming(model, reader, query_reader, T, weights);
native_predictions = pme.backmap_streaming(model, coordinates);
```

Readers return raw observation rows using one-based, inclusive bounds
`reader(first,last)`. The metric is a fixed vector or row reader. `native`
is `M`-by-`S`, already prepared in the desired native coordinate system.
Query coordinates are `T`-by-`N` and native predictions are `M`-by-`T`.
An optional seventh argument, `mode_writer(first,last,modes)`, receives
observation modes in a second pass. The default compact model stores no
observation matrix or reader handles and can be saved using `save`.
This compact model is separate from the regular `pme.run_case` model. The
standard runner retains the database in memory, even with `solver="snapshot"`.

- MATLAB and Python implementations follow the same configuration structure  
- JSON files define the full workflow  
- MATLAB is useful for validation and comparison with the reference implementation  
