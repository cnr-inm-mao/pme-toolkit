# Benchmarks

This directory contains the repository benchmark definitions used to run PME, PI-PME, and PD-PME workflows on the supported shape-optimization datasets.

## Layout

The benchmarks are organized first by **dataset-selection strategy** and then by **method family**:

```text
benchmarks/
├── standard/
│   ├── pme/
│   ├── pi_pme/
│   └── pd_pme/
└── goal_oriented/
    ├── pi_pme/
    └── pd_pme/
```

Each leaf benchmark folder typically contains JSON configuration files and a README describing the specific case.

## Benchmarks currently defined

The current repository contains benchmark folders for:

- `glider`
- `airfoil`

## Dataset availability

Benchmark folders define the workflow configuration, but the underlying datasets may not all be bundled in the repository.

At this stage:

- `glider` has repository-aligned dataset metadata under `databases/glider/`;
- `airfoil` has repository-aligned dataset metadata under `databases/airfoil/`;

## Recommended reproducible starting point

For a self-contained local validation run, use the tiny glider test case in `tests/`.
