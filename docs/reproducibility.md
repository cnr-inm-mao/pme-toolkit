# Reproducibility

PME-toolkit is designed to support reproducible dimensionality reduction workflows through:

- configuration-driven execution (JSON files)
- versioned datasets
- benchmark definitions

---

## Self-contained validation

The repository includes a minimal dataset and test cases for quick validation:

- data: `tests/data/`
- configurations: `tests/cases/`

These provide a fully self-contained workflow that can be executed without external dependencies.

### MATLAB

    run("tests/matlab/run_tests.m")

### Python

    pytest tests/python -q

## Snapshot validation

The snapshot tests compare a controlled spectrum with an independent symmetric
observation-covariance calculation. They check weighted orthonormality, complete
repeated eigenspaces, zero-weight native components, native reconstruction,
rank-deficient inputs, row-block assembly, and variance-based mode selection.

Both languages also use `tests/data/snapshot_parity.json` for PME, PI-PME, and
PD-PME. It contains the same geometry, native variables, physical fields and
scalars, including a constant source. To compare the current implementations:

```matlab
run("tests/matlab/run_tests.m")
export_snapshot_parity("snapshot_parity.json")
```

```bash
python tests/python/compare_snapshot_parity.py snapshot_parity.json
```

The MATLAB CI job runs this comparison after its test suite. It checks
eigenvalues, selected dimension, weights, sample subspaces, native
reconstructions, total variance and achieved retention with explicit tolerances.
Modes are compared through invariant quantities, so signs and rotations within
repeated eigenspaces do not create false failures.

The complete Python suite includes a benchmark workflow that may download an
external dataset. For the self-contained tests, use:

```bash
pytest tests/python -q --ignore=tests/python/test_run_case.py
```

---

## Benchmark reproducibility

Full benchmark runs rely on external datasets.

These datasets are:

- documented under `databases/`
- distributed via Zenodo
- referenced by benchmark configuration files

To reproduce benchmark results:

1. download the dataset from Zenodo  
2. place it locally  
3. update the `dbfile` path in the configuration  
4. run the benchmark  

---

## Configuration-driven workflow

All experiments are defined through JSON configuration files.

This ensures:

- reproducibility across environments  
- transparency of preprocessing and methods  
- portability of experiments  

---

## Notes

- results depend on dataset version and configuration  
- ensure consistency between dataset and JSON specification  
- benchmark cases provide reference configurations for reproducibility  
