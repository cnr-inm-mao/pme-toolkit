# Benchmarks

This directory contains **benchmark definitions and verification drivers** for
**PME**, **PI-PME** and **PD-PME** on the supported shape-optimization datasets
and controlled synthetic inputs.

Dataset benchmarks are defined through **JSON configuration files** and are
compatible with both **MATLAB and Python implementations**.

---

## Structure

Dataset cases are organized by **dataset-selection strategy** and **method
family** (`pme/`, `pi_pme/` or `pd_pme/`).

| Directory | Contents |
|---|---|
| `standard/` | Standard PME, PI-PME and PD-PME dataset cases |
| `goal_oriented/` | Goal-oriented PI-PME and PD-PME dataset cases |
| [`snapshot/`](snapshot/README.md) | Versioned driver for controlled direct, snapshot and streaming experiments |
| `results/` | Generated local reports; created on demand and excluded from Git |

Each dataset case folder typically contains:

- one or more `case.json` files  
- optional `backmapping.json` configurations  
- a local `README.md` describing the case  

---

## Supported datasets

The current repository includes benchmark configurations for:

- `glider`
- `airfoil`
- `propeller` (standard PME)

These datasets are described under:

- `databases/glider/`
- `databases/airfoil/`
- `databases/propeller/`

---

## Workflow

Each benchmark defines a **fully reproducible workflow** based on JSON configuration files.

A typical workflow consists of:

1. running PME / PI-PME / PD-PME:

       pme-run <case.json>

   or

       matlab -batch "run_pme('<case.json>')"

2. optionally running backmapping:

       pme-back <backmapping.json>

   or

       matlab -batch "run_back('<backmapping.json>')"

Outputs are written to the `outdir` specified in the JSON configuration.
Relative input and output paths are resolved against the configuration file's
directory. The standard runners load the database into memory.

## Solver selection

All eleven benchmark fitting cases explicitly set `"solver": "auto"`.
The shared case workflow selects `direct` when the number of positive-weight
observation rows is smaller than the sample count, and `snapshot` otherwise.
For solver comparisons, change this one field to `"direct"` or `"snapshot"`
while retaining the same dataset, filters, metric and confidence index.
Inputs that omit the field continue to use `auto` in both languages.

Backmapping configurations refer to the fitting case and saved model; they do
not have their own solver setting. Use only the backmapping examples actually
included in a case directory and supply their required reduced coordinates.

See [Snapshot formulation](../docs/snapshot.md) for the streamed reader API and
[Zenodo regression](../docs/zenodo-regression.md) for the complete airfoil
comparison against the preceding implementation.

## Controlled experiments and outputs

The [snapshot verification driver](snapshot/README.md) calls the public toolkit
APIs and uses the fixed input in `tests/data/snapshot_curve.json`. The driver,
input and execution instructions are versioned so that experiments can be
repeated with the corresponding toolkit revision.

Generated reports under `benchmarks/results/` are local outputs and must not be
committed. A selected reference report can be published as a release attachment
after running the documented protocol on that exact source revision. Preserve
its recorded revision, source hashes, environment and measured quantities.

---

## Dataset availability

Benchmark folders define **configuration and workflow**, while datasets may be:

- bundled (for testing purposes), or  
- referenced externally via metadata in `databases/`  

---

## Recommended starting point

For a fully reproducible and self-contained run, use:

    tests/cases/test_glider.json

This case relies on a lightweight dataset included in:

    tests/data/

---

## Notes

- Benchmarks are designed to be **implementation-independent**  
- The same JSON files can be executed with both MATLAB and Python  
- Cross-language consistency is ensured through regression testing on reference cases  
