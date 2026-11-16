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

These provide a small workflow that does not require an external dataset.

### MATLAB

    run("tests/matlab/run_tests.m")

### Python

    pytest tests/python -q --ignore=tests/python/test_run_case.py

The excluded integration test uses the complete external glider database.
Run `pytest tests/python -q` to include it; that run can download the benchmark
archive. The tiny fixture and the remaining local tests need no external data.

## Direct and snapshot validation

The snapshot tests compare a controlled spectrum with an independent symmetric
observation-covariance calculation. They check weighted orthonormality, complete
repeated eigenspaces, zero-weight native components, native reconstruction,
rank-deficient inputs, row-block assembly, and variance-based mode selection.
The `auto`, `direct` and `snapshot` choices use the same prepared data, metric
and numerical tolerances. The direct option is also exercised when the number
of observations is smaller than the number of samples.

Both languages also use `tests/data/snapshot_parity.json` for PME, PI-PME, and
PD-PME. It contains the same geometry, native variables, physical fields and
scalars, including a constant source. To compare the current implementations:

```matlab
run("tests/matlab/run_tests.m")
export_snapshot_parity("snapshot_parity.json")
```

```bash
python tests/python/compare_snapshot_parity.py snapshot_parity.json
```

The MATLAB CI job runs this comparison after its test suite. It checks
eigenvalues, selected dimension, weights, sample subspaces, native
reconstructions, total variance and achieved retention with explicit tolerances.
Modes are compared through invariant quantities, so signs and rotations within
repeated eigenspaces do not create false failures.

The complete Python suite includes a benchmark workflow that may download an
external dataset. For tests that do not require that download, use:

```bash
pytest tests/python -q --ignore=tests/python/test_run_case.py
```

## Streamed MATLAB and Python comparison

The fixture `tests/data/snapshot_curve.json` stores the same native construction
and query designs for both languages. The observation reader evaluates the
documented nonlinear curve at midpoint locations. The export checks resident
direct and snapshot results, optional observation-mode writing, cross-Gram
query encoding and a native-only fit with 1,048,576 observation rows:

```matlab
addpath("matlab/src")
addpath("tests/matlab")
export_streaming_parity("streaming_parity.json")
```

The MATLAB CI workflow compares the exported results with the current Python
implementation. Its comparisons use eigenvalues, selected sample subspaces
and native backmaps, accounting for the sign ambiguity of eigenvectors. The
large run also verifies that the reader never receives more rows than the
configured block size and that one fitting pass reads every row exactly once.

## Controlled manuscript experiments

Run the toolkit verification driver from the repository root, using the Python
package installed from that checkout:

```bash
python -m pip install -e ./python
python benchmarks/snapshot/verify_manuscript.py \
  --output benchmarks/results/snapshot_manuscript.json
```

The driver and the fixed native-input fixture are versioned. The report is a
generated local output: `benchmarks/results/` is created on demand and excluded
from Git. Each run overwrites the requested output file; choose a different
`--output` path to preserve multiple runs.

The driver calls the public `direct_decompose`, `snapshot_decompose`,
`fit_streaming`, `transform_streaming` and `backmap_streaming` APIs. It performs
four experiments:

| Experiment | Fixed setup | Main outputs |
|---|---|---|
| Prescribed spectrum | 160 observations, 48 samples, six native variables; eigenvalues $[4,1,1,0.1,0.01,0.001]$ | Positive eigenvalues, complete repeated eigenspaces, native backmaps, orthonormality and residuals |
| Geometric audit | 256 observation rows, 64 construction and 128 independent query designs, eight native variables | Retained variance, native error, modal error, regenerated-geometry error and domain violations |
| Conditioning | Six positive directions spanning 2, 6, 10, 12 and 14 decades | Resolved rank, eigenvalue error and native error including any discarded directions |
| Streamed scale | 1,048,576 rows, 64 construction samples, eight native variables, six retained modes, blocks of 2048 rows | Exact reader-call bounds, construction and query backmaps, elapsed times and process peak resident memory |

The geometric observations are

$$
y(t;u)=0.12\sin(\pi t)+
\sum_{j=1}^{8}\frac{0.04}{j^{1.2}}u_j\sin(j\pi t)+
0.025u_1u_2\sin(9\pi t),
\qquad u\in[-1,1]^8.
$$

The metric is uniform $1/Q$. Native designs are fixed in
`tests/data/snapshot_curve.json`: NumPy `default_rng(20261020)`, first a uniform
draw of shape `(8,64)`, then one of shape `(8,128)`. The explicit fixture removes
any dependence on another language's random generator or array-filling order.
The confidence target for the six-mode streamed case is fixed between the
five-mode and six-mode cumulative fractions of the 256-row case. The large
case has the same discrete inner products for this sine family, providing an
independent small resident-data reference for its spectrum and native backmap.

The JSON output records the protocol, source-file SHA256 values, repository
revision, whether the working tree was modified, Python and NumPy versions,
cutoffs and all measured quantities. It uses one numerical-library thread.
The large case runs in a separate process, so peak resident memory includes the
interpreter, imported libraries, inputs and temporary arrays without carrying
allocations from the preceding experiments. Analytical array sizes are reported
separately. Timings are single observations from that environment, not a repeated
performance study or measurements of file I/O.

For a release or manuscript reference, run this protocol on the exact source
revision being cited, with a clean working tree, and publish the selected report
as a release attachment. Preserve its recorded provenance and measurements.
Report publication is a separate step from running the driver; routine local
outputs should remain unversioned.

Use `--skip-large` to run only the smaller checks, or `--large-rows Q` to change
the streamed resolution. These arguments are recorded through the output
dimensions. The retained spectrum and native reconstructions are compared with
explicit tolerances; no historical manuscript numbers are hard-coded as a
reference.

The archived reference scripts used by earlier manuscript drafts are not part
of these inputs. Sharing a seed does not specify their draw order. Manuscript
tables and statements about the implementation must use the measured toolkit
outputs and cite their version, rather than relabelling earlier results.

## Benchmark reproducibility

Full benchmark runs rely on external datasets.

These datasets are:

- documented under `databases/`
- distributed via Zenodo
- referenced by benchmark configuration files

Run a supplied `benchmarks/**/case.json` with either case runner. Missing data
are obtained from the matching `databases/<name>/dataset.json` metadata. For a
manual download, extract the archive and set the configuration paths relative
to its case directory. The examples explicitly set `solver="auto"`; existing
inputs that omit the field still default to that choice. Set `direct` and
`snapshot` explicitly when comparing their numerical results on the same case.

### Zenodo regression against the preceding implementation

The [Zenodo airfoil regression](zenodo-regression.md) compares PME, PI-PME and
PD-PME on the complete published RAE2822 database with the unchanged
implementation at commit `68309805e9aff5a9b877c33982c7181d8faa550b`. It checks the
dataset hash, uses the existing standard-case sample filters, and does not take
a smaller sample subset for the snapshot calculation.

The regression checks explained variance, resolved positive eigenvalues,
weighted eigenvectors and native backmaps against both the historical solver
and an independent symmetric direct reference. It aligns isolated eigenvectors
by sign and compares repeated clusters through their invariant subspaces.
Current and historical MATLAB exports can be included in the same report.
The linked protocol documents the exact dataset, tolerances, commands and CI
artifacts. This full-dataset check is separate from the small unit suite.

---

## Configuration-driven workflow

Standard case experiments use JSON configuration files. The controlled
streaming experiments use the versioned verification driver and the explicit
native-sample fixture described above.

This ensures:

- reproducibility across environments  
- transparency of preprocessing and methods  
- portability of experiments  

---

## Notes

- results depend on dataset version and configuration  
- ensure consistency between dataset and JSON specification  
- benchmark cases provide reference configurations for reproducibility  
