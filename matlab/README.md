# MATLAB implementation

This folder contains the **MATLAB implementation** of PME-toolkit.

## Scope

The MATLAB code supports the repository workflow for:

- **PME**
- **PI-PME**
- **PD-PME**
- analytical **backmapping** to the original parametric variables

within the current **shape-optimization** scope of the project.

The implementation is fully integrated in the **JSON-driven workflow** used across the repository.

The v1.3.0 fitting workflow accepts `solver="auto"`, `"direct"` or
`"snapshot"` in the shared case JSON. The field is optional and defaults to
`auto`; all distributed fitting examples declare it explicitly. Both solvers
use the same preprocessing, metric, mode selection and model interface.

## Role within PME-toolkit

PME-toolkit provides a **dual MATLAB/Python implementation**.

The MATLAB code:

- shares the same **configuration format (JSON)** as the Python implementation
- produces outputs compatible with the repository test and benchmark workflows
- is validated through **cross-language regression tests**

## Location of the source code

The MATLAB package is located under:

    matlab/src/+pme/

Typical entry points include:

- JSON-driven runners at repository root:
  - `run_pme.m`
  - `run_back.m`
- core functions under the `+pme` package

## Running the code

### Direct usage

From repository root:

    addpath(genpath("matlab/src"));
    out = pme.run_case("tests/cases/test_glider.json");

Backmapping:

    addpath(genpath("matlab/src"));
    out = pme.backmapping("tests/cases/test_glider_back.json", "x01", [0.1; 0.7; 0.3; 0.9; 0.2]);

### Wrapper-based execution

Thin wrappers are available at repository root:

    run_pme("benchmarks/standard/pme/glider/case.json");
    run_back("benchmarks/standard/pme/glider/backmapping.json");

These mirror the benchmark workflow and automatically handle:

- path setup
- output directory resolution
- model persistence for backmapping

Set `io.save_model=true` in the fitting case when a subsequent backmapping
run needs `model.mat`. Both the direct API and `run_pme` honor this setting.

## Outputs

Running a PME case generates:

- `model.mat` → reduced model when `io.save_model=true` (used for backmapping)
- `report.mat` → summary of the reduction (including `nconf`, NMSE, etc.)

Outputs are written to the `outdir` specified in the JSON case file.
Relative paths are resolved against the JSON file's directory.

## Streamed observations

`pme.fit_streaming`, `pme.transform_streaming` and `pme.backmap_streaming`
provide a reader-based snapshot workflow for observations stored or generated
in row blocks. The usual `pme.run_case` workflow keeps the input database in
memory even when `solver="snapshot"`. See the
[MATLAB API](../docs/matlab_api.md) and
[streamed formulation](../docs/snapshot.md#streamed-observations-and-compact-native-models)
for the reader, weight and native-variable contracts.

## Datasets

Some benchmark cases rely on external datasets referenced under:

    databases/

The regression tests use a **self-contained tiny dataset** under:

    tests/data/

## Testing

Run the MATLAB test suite from repository root:

    matlab -batch "cd('tests/matlab'); run_tests"

The test suite includes:

- configuration loading
- PME execution
- backmapping
- regression consistency checks
- direct/snapshot agreement, numerical rank and repeated eigenvalue clusters
- streamed fitting, query projection and native backmapping

CI also compares current MATLAB/Python outputs and runs the complete Zenodo
airfoil regression described in [Reproducibility](../docs/reproducibility.md).

## Status

The MATLAB implementation is **fully functional** for PME, PI-PME, and PD-PME within the current repository scope and is maintained in alignment with the Python implementation.
