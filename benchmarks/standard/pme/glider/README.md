# Standard benchmark — PME — glider

This case runs PME on the glider dataset with the standard sample-selection settings in `case.json`.
The same JSON configuration is used by MATLAB and Python.

## Solver

The case explicitly sets `"solver": "auto"`. The fit selects the smaller
direct or snapshot eigenproblem. Use `"direct"` or `"snapshot"` to select
a solver explicitly; omitting the field also defaults to `"auto"`.
See the [solver documentation](../../../../docs/snapshot.md).

## Run

After [installation](../../../../docs/quickstart.md), run from the repository root:

```bash
pme-run benchmarks/standard/pme/glider/case.json
```

or:

```bash
matlab -batch "run_pme('benchmarks/standard/pme/glider/case.json')"
```

The [dataset metadata](../../../../databases/glider/dataset.json) describes
the external data. Missing dataset files are downloaded by the case runner.
Outputs are written to `io.outdir`, relative to the case directory.

## Backmapping

Run the fit first to save the model for the selected language.
The supplied `backmapping.json` reads the example coordinates from `x01.txt`.
If the fit settings change the retained dimension, keep the requested
`reduced_space.nconf` and input length consistent with the saved model.

```bash
pme-back benchmarks/standard/pme/glider/backmapping.json
```

or:

```bash
matlab -batch "run_back('benchmarks/standard/pme/glider/backmapping.json')"
```
