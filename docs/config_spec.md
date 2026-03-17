
# Configuration specification

PME-toolkit uses JSON configuration files to define dimensionality reduction workflows.

This page documents the **actual configuration schema** used by the toolkit.

---

## Full example

    {
      "mode": "pi",
      "CI": 0.95,
      "baseline_col": 0,
      "geom": { ... },
      "vars": { ... },
      "phys": { ... },
      "filters": { ... },
      "io": { ... }
    }

---

## Top-level fields

### `mode`

Type: string  

Defines the method:

- `"pme"` → geometry + variables  
- `"pi"` → physics-informed PME  
- `"pd"` → physics-driven PME  

---

### `CI`

Type: float  

Confidence index (retained variance), e.g.:

    0.95 → 95% retained variance

---

### `baseline_col`

Type: integer  

Index of the baseline configuration in the dataset.

Used for:

- normalization
- fixed-variable handling

---

## Geometry (`geom`)

Defines the geometric structure.

### Fields

- `Jdir` (int)  
  Number of spatial directions per point  
  (e.g. 2 → 2D, 3 → 3D)

- `patches` (list)

Each patch:

    {
      "name": "P1",
      "K": 784
    }

Where:

- `name` → identifier  
- `K` → number of points in the patch  

### Notes

Total geometric dimension:

    n_geom = Jdir × sum(K over patches)

---

## Variables (`vars`)

Defines parametric design variables.

### Fields

- `Mbase` (int)  
  Total number of variables

- `idx_active` (list)  
  Indices of active variables  

    [] → all variables active

- `fixed_policy` (string)

    "baseline" → fixed variables set to baseline values

- `Urange_file` (string)  
  Path to variable bounds

- `use_db_range_if_missing` (bool)  
  Fallback to database if range file is missing

---

## Physics (`phys`)

Defines physical data used in PI-PME / PD-PME.

### Fields

#### `fields`

List of distributed fields:

    {
      "name": "Cp",
      "nCond": 1,
      "disc": { "K": 784 }
    }

Where:

- `name` → field name  
- `nCond` → number of conditions  
- `disc.K` → discretization size  

---

#### `scalars`

List of scalar quantities:

    {
      "name": "D",
      "nCond": 1
    }

---

### Notes

- fields → spatially distributed data  
- scalars → global quantities  

---

## Filters (`filters`)

Defines dataset filtering.

### Fields

#### `remove_nan` (bool)

Remove samples containing NaN values.

---

#### `goal`

    {
      "enable": true,
      "metrics": [
        {
          "c_offset": 0,
          "rule": "positive"
        }
      ]
    }

- `enable` → activate filter  
- `metrics` → list of constraints  

Each metric:

- `c_offset` → column index in scalar outputs  
- `rule` → filtering rule (e.g. `"positive"`)

---

#### `iqr`

    {
      "enable": true
    }

Apply interquartile range filtering.

---

## Input / Output (`io`)

Defines data access and output behavior.

### Fields

- `dbfile` (string)  
  Path to database file (`.mat`)

- `transpose_if` (string)

    "never" | "always" | "auto"

Controls data orientation.

---

- `outdir` (string)  
  Output directory

- `save_model` (bool)  
  Save trained model

---

## Backmapping configuration

Backmapping uses a different JSON structure:

    {
      "model_path": "results/model.mat",
      "x": [ ... ]
    }

Where:

- `model_path` → trained model  
- `x` → reduced coordinates vector  

---

## Key constraints

- all data must be sample-aligned  
- geometry, variables, and physics must share sample count  
- `x` dimension must match retained modes  
- paths must be valid and accessible  

---

## Minimal working example

    {
      "mode": "pme",
      "CI": 0.99,
      "baseline_col": 0,
      "geom": {
        "Jdir": 3,
        "patches": [
          { "name": "P1", "K": 100 }
        ]
      },
      "vars": {
        "Mbase": 10,
        "idx_active": [],
        "fixed_policy": "baseline"
      },
      "filters": {
        "remove_nan": true
      },
      "io": {
        "dbfile": "database.mat",
        "outdir": "results",
        "save_model": true
      }
    }

---

## Summary

The configuration file fully defines:

- data structure  
- preprocessing  
- method  
- output  

and is the central interface of PME-toolkit.

Backmapping uses a separate configuration format (see Backmapping page).
