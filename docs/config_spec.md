
# Configuration specification

PME-toolkit uses JSON configuration files to define dimensionality reduction workflows.

This page documents the **actual configuration schema** used by the toolkit.

---

## Configuration outline

The following outline abbreviates the nested objects. A complete runnable
reference configuration is shown at the end of this page.

    {
      "mode": "pi",
      "solver": "auto",
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

Type: float, default `0.99`.

Confidence index (retained variance), e.g.:

    0.95 → 95% retained variance

The valid interval is `(0, 1]`. Retention is measured against the complete
weighted covariance/Gram trace, before numerical rank truncation. If the selected
boundary intersects a repeated eigenvalue cluster, the whole cluster is kept.
If the resolved spectrum cannot reach the requested `CI`, all resolved modes
are retained and a warning reports the achieved fraction.

### `solver` (optional)

Type: string, default `"auto"`.

This field is optional for existing configurations. The distributed fitting
examples and benchmarks declare `"solver": "auto"` explicitly for clarity.
An omitted field selects `auto`; an empty string, `null`, or an unsupported
value is invalid.

- `"auto"`: solve the smaller symmetric eigenproblem. Use the direct
  covariance when the number of positive-weight observation rows is smaller
  than the sample count; use the snapshot Gram otherwise.
- `"direct"`: explicitly solve the positive-weight observation covariance.
- `"snapshot"`: explicitly solve the sample-space Gram matrix.

Both formulations use the same fixed weights, positive-rank cutoff, complete
eigenvalue clusters, trace-based confidence criterion, and native backmap.
The selected solver and its matrix dimension are reported in the model
diagnostics. The separate `fit_streaming` API always uses snapshot assembly.

### `snapshot` (optional)

The same numerical options apply to both solvers in MATLAB and Python:

| Field | Default | Meaning |
| --- | --- | --- |
| `eig_rtol` | `S * eps` | Relative cutoff against the largest eigenvalue, with a minimum of `S * eps`; `S` is the number of retained samples and `eps` is double-precision machine epsilon. |
| `eig_atol` | `0` | Absolute eigenvalue cutoff. |
| `cluster_rtol` | `1e-10` | Relative gap tolerance for keeping an entire eigenvalue cluster. |
| `block_rows` | `4096` | Maximum rows per weighted Gram assembly block. |

Eigenvalues must satisfy `lambda > max(eig_atol, eig_rtol * lambda_max)`.
Adjacent resolved eigenvalues are treated as one cluster when their gap is at
most the larger of that cutoff and `cluster_rtol` times the larger eigenvalue.
Tolerances must be finite and nonnegative; `block_rows` must be a positive integer.
The requested relative cutoff, its effective value after the numerical floor,
and achieved retention are stored in the model diagnostics. Setting the
requested relative cutoff to zero does not disable the roundoff protection.
See [Snapshot formulation](snapshot.md) for storage, numerical limits, and
compatibility details.

---

### `baseline_col`

Type: integer  

Index of the baseline configuration in the dataset.
Indices in JSON files are **zero-based**: `0` selects the first sample.
MATLAB converts JSON indices to its internal one-based convention when reading
the case. This also applies to active-variable indices and filter indices.

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
  Zero-based indices of active variables in the JSON file

    [] → all variables active

- `fixed_policy` (string)

    "baseline" → fixed variables set to baseline values

- `Urange_file` (string)  
  Path to variable bounds

- `use_db_range_if_missing` (bool)  
  Derive ranges from the database when no ranges are supplied (default `true`).
  An explicitly named range file must be accessible; remove an unused path
  rather than naming a nonexistent file.

---

## Physics (`phys`)

Defines physical data used in PI-PME / PD-PME.

For `mode: "pi"` or `mode: "pd"`, `phys` must contain at least one entry in
`fields` or `scalars`. Either source type alone is sufficient. A missing,
null, or empty `phys` block (including two empty source lists) raises a clear
configuration error in both MATLAB and Python, before case data is loaded
or downloaded. The same validation applies to direct fitting calls.

For portable MATLAB/Python case files, include both `fields` and `scalars`
lists, leaving any unused list empty. For geometry-only PME, select
`mode: "pme"` and leave both lists empty. Direct fitting calls also accept
PME configurations with `phys` omitted. PI/PD never silently fall back to
geometry-only PME.

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

Remove samples containing nonfinite values (NaN or infinity).

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

- `c_offset` → zero-based row offset within the scalar block `C`
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
Relative `dbfile`, `Urange_file` and `outdir` paths are interpreted from the
directory containing the fitting JSON file, not from the current working
directory. The standard runner reads the database into memory for every solver.

### Fields

- `dbfile` (string)  
  Path to database file (`.mat`)

- `transpose_if` (string)

    "never" | "always" | "auto"

Controls data orientation. `never` preserves feature rows and sample columns;
`always` transposes the input; `auto` uses the configured row count to choose
the orientation. The portable MAT database variable names are `database` and
`DB`.

---

- `outdir` (string)  
  Output directory; defaults to `results` under the fitting case directory
  in both languages.

- `save_model` (bool)  
  Save the fitted model (`model.npz` in Python, `model.mat` in MATLAB).
  The default is `true`. Setting `false` disables model-file writes without
  deleting an existing model or removing the in-memory result.
  Set this to `true` when the subsequent standalone backmapping workflow
  needs to read that model. Reporting writes `report.mat`.

---

## Backmapping configuration

Backmapping has a separate JSON schema beginning with `case_json`, `input`,
`reduced_space`, `denorm` and `output`. It reads the fitted model and therefore
does not need `solver` or `snapshot` settings. See
[Backmapping configuration](backmapping_config.md) for the supported fields,
coordinate normalization and path rules.

---

## Key constraints

- all data must be sample-aligned  
- geometry, variables, and physics must share sample count  
- `x` dimension must match retained modes  
- paths must be valid and accessible  

---

## Minimal working example

The following configuration uses the included tiny glider data. Its relative
paths assume a file under `tests/cases/`, as in `test_glider.json`:

    {
      "mode": "pme",
      "solver": "auto",
      "CI": 0.99,
      "baseline_col": 0,
      "geom": {
        "Jdir": 3,
        "patches": [
          { "name": "P1", "K": 784 }
        ]
      },
      "vars": {
        "Mbase": 32,
        "idx_active": [],
        "fixed_policy": "baseline",
        "Urange_file": "../data/glider_range.mat",
        "use_db_range_if_missing": true
      },
      "phys": { "fields": [], "scalars": [] },
      "filters": {
        "remove_nan": true
      },
      "io": {
        "dbfile": "../data/glider_tiny.mat",
        "transpose_if": "never",
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
