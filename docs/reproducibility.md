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

    run("tests/run_tests.m")

### Python

    pytest tests/python -q

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
