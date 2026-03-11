# Python package

This folder contains the **Python scaffold** for PME-toolkit.

## Current status

The Python side of the repository is **not yet a feature-complete port** of the MATLAB reference implementation.

At this stage it mainly provides:

- package structure for the future Python implementation;
- configuration loading utilities;
- a minimal test validating JSON configuration handling.

## What is currently reliable

The currently reliable Python workflow is limited to:

```bash
cd python
PYTHONPATH=src pytest -q
```

This checks the configuration loader against the benchmark-style JSON structure used in the repository.

## What is not yet implemented

The following repository capabilities should still be considered MATLAB-only at this stage:

- full PME model construction;
- PI-PME and PD-PME workflows;
- production backmapping;
- benchmark execution parity with MATLAB.

## Packaging

The package metadata is defined in:

```text
python/pyproject.toml
```

Source code lives under:

```text
python/src/pme_toolkit/
```

## Recommendation

Use MATLAB for actual dimensionality-reduction studies in the current repository state, and treat the Python package as infrastructure for the forthcoming port.
