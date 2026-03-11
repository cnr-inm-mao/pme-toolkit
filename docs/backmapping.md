# Backmapping

Backmapping is one of the key features of PME-based dimensionality reduction.
It reconstructs the original parametric variables from reduced coordinates using the learned embedding.

## MATLAB usage

```matlab
addpath(genpath("matlab/src"));
out = pme.backmapping("tests/cases/test_glider_back.json", "x01", [0.1; 0.7; 0.3; 0.9; 0.2]);
```

Repository-root wrapper:

```matlab
run_back("benchmarks/standard/pme/glider/backmapping.json");
```

## Notes

The exact configuration depends on the JSON case and the corresponding trained reduction data.
