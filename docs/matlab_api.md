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

`pme.snapshot_decompose(Pc, w, options)` exposes the snapshot solver for
already centered data with samples in columns. Its result contains resolved
eigenvalues, complete modes, training coordinates, sample eigenvectors and
diagnostics. `pme.weights_diag` builds vector weights for the normal fitting
path. `pme.direct_decompose(Pc, w, options)` exposes the equivalent symmetric
observation covariance solver. `pme.decompose(Pc, w, options, solver)` accepts
`'auto'`, `'direct'`, or `'snapshot'`; regular fitting uses `cfg.solver` with
default `'auto'`. See [Snapshot formulation](snapshot.md) for numerical options and
compatibility with legacy models.

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

- MATLAB and Python implementations follow the same configuration structure  
- JSON files define the full workflow  
- MATLAB is useful for validation and comparison with the reference implementation  
