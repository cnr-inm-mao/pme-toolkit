# Reproducibility

## Self-contained repository validation

The repository includes a tiny glider dataset under `tests/data/` and corresponding JSON configurations under `tests/cases/`.
This is the most reliable self-contained validation workflow in the current snapshot.

Run the MATLAB tests with:

```matlab
run("tests/run_tests.m")
```

Run Python tests with:

    pytest tests/python -q

## External benchmark datasets

Some benchmark runs depend on external datasets referenced through the metadata under `databases/`.
