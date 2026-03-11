# Python API

The Python package is currently a **minimal scaffold** rather than a full port of the MATLAB implementation.

## Current scope

At this stage the Python side provides:

- package layout;
- configuration loading utilities;
- a minimal test targeting the benchmark-style JSON structure.

## Recommended usage

```bash
cd python
PYTHONPATH=src pytest -q
```

## Status note

Use MATLAB for the current production workflow and treat Python as the starting point for the forthcoming implementation.
