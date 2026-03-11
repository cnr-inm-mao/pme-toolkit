# MATLAB API

The MATLAB implementation is the current reference implementation of PME-toolkit.

## Main usage pattern

Add the package to the MATLAB path:

```matlab
addpath(genpath("matlab/src"));
```

Then run a case through the package entry points, for example:

```matlab
out = pme.run_case("tests/cases/test_glider.json");
```

or perform backmapping directly:

```matlab
out = pme.backmapping("tests/cases/test_glider_back.json", "x01", [0.1; 0.7; 0.3; 0.9; 0.2]);
```

## Wrappers

Repository-root wrappers are also available:

- `run_pme.m`
- `run_back.m`

These wrap the JSON-driven workflow used in the benchmark folders.
