# Quickstart

## MATLAB

The most reliable self-contained run in the repository is the tiny glider test case shipped under `tests/`.

```matlab
addpath(genpath("matlab/src"));
out = pme.run_case("tests/cases/test_glider.json");
```

For standalone backmapping:

```matlab
addpath(genpath("matlab/src"));
out = pme.backmapping("tests/cases/test_glider_back.json", "x01", [0.1; 0.7; 0.3; 0.9; 0.2]);
```

You can also use the root-level wrappers for benchmark-style runs:

```matlab
run_pme("benchmarks/standard/pme/glider/case.json");
run_back("benchmarks/standard/pme/glider/backmapping.json");
```

## Python

At this repository stage, the Python package only provides a minimal scaffold and configuration-loader test:

```bash
cd python
PYTHONPATH=src pytest -q
```

## Documentation

Build the documentation site locally with:

```bash
mkdocs serve
```
