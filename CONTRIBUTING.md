# Contributing to PME-toolkit

Thank you for your interest in contributing to **PME-toolkit**.

The project is currently developed primarily as a research software repository, but contributions and suggestions are welcome.

---

# Types of contributions

Contributions may include:

* bug reports
* documentation improvements
* benchmark extensions
* code improvements
* Python port contributions
* additional test cases

---

# Reporting issues

Please use the GitHub **Issues** tab to report:

* bugs
* unexpected behavior
* documentation inconsistencies
* installation or execution problems

When reporting an issue, please include:

* operating system
* MATLAB or Python version
* exact command used
* error message (if any)

---

# Development workflow

The recommended workflow is:

1. Fork the repository
2. Create a feature branch

```
git checkout -b feature/my_feature
```

3. Implement the change
4. Run tests
5. Open a pull request

---

# Code style

## MATLAB

* follow MATLAB package structure (`+pme`)
* avoid global variables
* keep functions small and modular
* document functions with MATLAB help blocks

## Python

* follow PEP8 where applicable
* place code under `python/src/pme_toolkit/`
* include tests when adding functionality

---

# Testing

Before submitting a pull request, please run the repository tests.

### MATLAB

```
run("tests/run_tests.m")
```

### Python

```
cd python
PYTHONPATH=src pytest -q
```

---

# Benchmarks and datasets

When adding new benchmark cases:

* place them under `benchmarks/`
* include a README describing the case
* document dataset dependencies in `databases/`

Large datasets should **not be stored directly in Git**.

---

# License

By contributing to this project you agree that your contributions will be released under the repository license (MIT).

