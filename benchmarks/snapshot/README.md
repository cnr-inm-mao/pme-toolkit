# Controlled snapshot experiments

`verify_manuscript.py` runs controlled experiments using the public toolkit
functions `direct_decompose`, `snapshot_decompose`, `fit_streaming`,
`transform_streaming` and `backmap_streaming`.

The experiments cover a prescribed spectrum with repeated eigenvalues,
geometric reconstruction, conditioning and a streamed case with 1,048,576
observation rows. The fixed native construction and query designs are stored
in [`tests/data/snapshot_curve.json`](../../tests/data/snapshot_curve.json),
which is also used for the MATLAB and Python streaming comparison.

## Run

From the repository root, install the Python package from the current checkout
and run the driver:

```bash
python -m pip install -e ./python
python benchmarks/snapshot/verify_manuscript.py
```

| Option | Effect |
|---|---|
| `--output PATH` | Write the JSON report to `PATH`; the default is `benchmarks/results/snapshot_manuscript.json` under the repository root |
| `--skip-large` | Run only the smaller experiments |
| `--large-rows Q` | Set the streamed observation count; the default is 1,048,576 and the minimum is 256 |

The output directory is created when needed. An existing file at the output
path is overwritten; use distinct output names to retain multiple runs.

## Source and generated results

This driver and its input fixture are part of the versioned reproducibility
materials. Reports under `benchmarks/results/` are generated local outputs,
excluded from Git. They record numerical comparisons, timings, process memory,
source hashes, repository revision and execution environment.

A reference report for a release or manuscript should be generated from the
exact source revision being cited, with a clean working tree, and published
separately as a release attachment. Preserve its original provenance and
measurements. Running the driver creates a local report; it does not publish
one automatically.

See [Reproducibility](../../docs/reproducibility.md#controlled-manuscript-experiments)
for the experimental protocol, tolerances and interpretation of the results,
and [Snapshot formulation](../../docs/snapshot.md) for the solver and streaming
APIs.
