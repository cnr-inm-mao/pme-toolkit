# MATLAB implementation

This folder contains the **reference implementation** of PME-toolkit for the current repository stage.

## Scope

The MATLAB code currently supports the repository workflow for:

- **PME**
- **PI-PME**
- **PD-PME**
- analytical **backmapping** to the original parametric variables

within the present **shape-optimization** scope of the project.

## Location of the source code

The MATLAB package is located under:

```text
matlab/src/+pme/
```

Typical entry points include the JSON-driven runners exposed at repository root:

- `run_pme.m`
- `run_back.m`

and the package functions under `+pme`.

## Recommended way to run the code

From repository root:

```matlab
addpath(genpath("matlab/src"));
out = pme.run_case("tests/cases/test_glider.json");
```

For backmapping:

```matlab
addpath(genpath("matlab/src"));
out = pme.backmapping("tests/cases/test_glider_back.json", "x01", [0.1; 0.7; 0.3; 0.9; 0.2]);
```

You can also use the thin wrappers:

```matlab
run_pme("benchmarks/standard/pme/glider/case.json");
run_back("benchmarks/standard/pme/glider/backmapping.json");
```

## Notes on datasets

Some benchmark cases rely on external datasets referenced under `databases/`.
The self-contained regression tests instead use the bundled tiny glider dataset under `tests/data/`.

## Status

At this release stage, MATLAB should be considered the **authoritative implementation** of the toolbox behavior.
