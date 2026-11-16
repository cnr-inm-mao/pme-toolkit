# Workflow

This page describes the standard PME-toolkit workflow from input data to outputs.

PME-toolkit is organized as a **configuration-driven pipeline**:

1. define the input dataset
2. define the workflow in a JSON configuration file
3. run dimensionality reduction
4. inspect results and visualizations
5. optionally perform backmapping

---

## 1. Input dataset

A PME workflow starts from a dataset containing one or more of the following components:

- geometry
- design variables
- physical information

These components must be **sample-aligned**, i.e. each sample must refer to the same design configuration across all data sources.

The dataset is typically stored in an external `.mat` file and referenced in the configuration through:

    "io": {
      "dbfile": "path/to/database.mat"
    }

See the *Datasets* and *Input data* pages for details.

---

## 2. JSON configuration

The workflow is fully defined through a JSON file.

A standard run configuration specifies:

- method (`mode`)
- eigensolver (`solver`: `auto`, `direct` or `snapshot`)
- retained variance (`CI`)
- geometry definition (`geom`)
- design variables (`vars`)
- physical quantities (`phys`, if applicable)
- filters (`filters`)
- input/output settings (`io`)

This JSON file is the central entry point of the workflow.
Existing inputs may omit `solver`; both implementations then use `auto`.
The distributed fitting examples declare it explicitly.

See the *Configuration specification* page.

---

## 3. Preprocessing

Before dimensionality reduction, the dataset may be filtered and normalized.

Available preprocessing steps include:

- removal of samples containing nonfinite values
- goal-oriented filtering
- IQR-based filtering
- variable-range handling

These operations are controlled in the `filters` and `vars` sections of the configuration file.

---

## 4. Dimensionality reduction

PME-toolkit supports three main modes:

- `pme` → geometry + variables
- `pi` → physics-informed reduction
- `pd` → physics-driven reduction

The workflow constructs the embedding from the data described in the configuration and retains the number of modes required to satisfy the confidence index:

    CI = retained variance threshold

Typical values are:

- `0.95`
- `0.99`

The result is a reduced latent representation of the original design space.
The `solver` choice changes the eigensolve and mode recovery within this common
workflow. `direct` solves the weighted covariance on positive-weight observation
rows; `snapshot` solves the sample Gram matrix; `auto` chooses the smaller one.
Both share the same numerical-rank cutoff and use the full weighted trace as
the retained-variance denominator. The selection includes a complete repeated
eigenvalue cluster at the confidence boundary. If the resolved spectrum cannot
reach `CI`, the model reports the achieved fraction and emits a warning.

The standard case runner loads the full database into memory. Selecting
`snapshot` does not switch the file loader to streaming. For observations read
from disk or generated in blocks, use the [streamed API](snapshot.md#streamed-observations-and-compact-native-models).

---

## 5. Outputs

A standard run produces:

- reduced coordinates
- retained dimensionality
- eigenvalues and modes
- reconstruction metrics
- saved model
- visualization outputs

Results are typically written under:

    results/

depending on the `io.outdir` setting.
Relative paths in the fitting configuration are interpreted from the directory
containing that configuration. Model files are `model.npz` in Python and
`model.mat` in MATLAB; both workflows produce `report.mat`.

---

## 6. Visualization

Visualization is part of the standard workflow and helps interpret the quality of the embedding.

Typical outputs include:

- scree plot
- retained variance
- variance by source
- NMSE by source
- variable participation
- geometric modes

These plot families are shared by direct and resident snapshot fitting.
PD-PME does not include a geometry block in its embedding and therefore does
not produce geometric-mode plots. The compact streaming API requires an
observation-mode writer and geometry metadata for corresponding mode plots.

See the *Visualization* page.

---

## 7. Backmapping

After a model has been generated, reduced coordinates can be mapped back to the original variable space through a separate backmapping workflow.

Backmapping requires:

- the original case configuration
- reduced coordinates input
- a dedicated backmapping JSON file

The backmapping file does not need a solver setting: it uses the saved model.

Run it with:

### Python

    pme-back tests/cases/test_glider_back.json

### MATLAB

    run_back("tests/cases/test_glider_back.json")

See the *Backmapping* and *Backmapping configuration* pages.

---

## 8. Typical execution

### Python

    pme-run tests/cases/test_glider.json

### MATLAB

    run_pme("tests/cases/test_glider.json")

These commands execute the full workflow on the self-contained glider reference case.

---

## Summary

The PME-toolkit workflow is:

- data-driven
- configuration-driven
- reproducible
- modular

The same logic applies to standard tests, benchmark cases, and externally hosted datasets.
