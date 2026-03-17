# Datasets

PME-toolkit operates on datasets stored in external files (typically `.mat`) and referenced through configuration files.

---

## Dataset organization

Dataset metadata is documented in:

- `databases/glider/`
- `databases/airfoil/`

These folders describe:

- dataset structure  
- variable definitions  
- required files  

---

## Benchmark datasets

The main benchmark datasets are distributed via Zenodo:

### Glider

    Serani, A., & Palma, G. (2026).
    Design-Space Dimensionality Reduction Benchmark Dataset – Bio-Inspired Underwater Glider (1.1) [Data set].
    https://doi.org/10.5281/zenodo.18936594

---

### Airfoil

    Serani, A., & Quagliarella, D. (2026).
    Design-Space Dimensionality Reduction Benchmark Dataset – RAE2822 Airfoil (1.0) [Data set].
    https://doi.org/10.5281/zenodo.18958555

---

## Dataset file

The dataset is specified in the configuration file:

    "io": {
        "dbfile": "path/to/database.mat"
    }

The file typically contains:

- geometric data  
- design variables  
- optional physical quantities  

---

## Data structure

Datasets are organized **sample-wise**, where:

- each column represents one design configuration  
- all data sources are aligned across samples  

The dataset may include:

### Geometry

- discretized coordinates  
- structured according to `geom` definition  

---

### Variables

- parametric design variables  
- dimension defined by `vars.Mbase`  

---

### Physics (optional)

- distributed fields (e.g. pressure coefficients)  
- scalar quantities (e.g. drag, lift)  

---

## Consistency requirements

All dataset components must:

- have the same number of samples  
- be aligned across geometry, variables, and physics  
- be free of missing values (after filtering)

---

## Usage

To use a dataset:

1. download the dataset from Zenodo  
2. extract it locally  
3. update the `dbfile` path in the JSON configuration  
4. run the benchmark  

---

## Notes

- dataset structure must match the configuration file  
- geometry, variables, and physics must match `geom`, `vars`, and `phys`  
- incorrect alignment will lead to invalid results  

---

## Summary

Datasets provide the input to PME workflows and must be:

- versioned (via Zenodo)  
- structured consistently  
- correctly referenced in configuration files  
