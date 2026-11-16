# Standard benchmark — PME — propeller

This case runs PME on the propeller dataset with the standard sample-selection settings in `case.json`.
The same JSON configuration is used by MATLAB and Python.

## Solver

The case explicitly sets `"solver": "auto"`. The fit selects the smaller
direct or snapshot eigenproblem. Use `"direct"` or `"snapshot"` to select
a solver explicitly; omitting the field also defaults to `"auto"`.
See the [solver documentation](../../../../docs/snapshot.md).

## Run

After [installation](../../../../docs/quickstart.md), run from the repository root:

```bash
pme-run benchmarks/standard/pme/propeller/case.json
```

or:

```bash
matlab -batch "run_pme('benchmarks/standard/pme/propeller/case.json')"
```

The [dataset metadata](../../../../databases/propeller/dataset.json) describes
the external data. Missing dataset files are downloaded by the case runner.
Outputs are written to `io.outdir`, relative to the case directory.

## Backmapping

Run the fit first to save the model for the selected language.
Provide `x01.txt` in this case directory before running the supplied
`backmapping.json`: it requests five normalized reduced coordinates
in `[0, 1]`. Confirm that the fitted model retains at least five modes,
or change `reduced_space.nconf` and the input length together.

```bash
pme-back benchmarks/standard/pme/propeller/backmapping.json
```

or:

```bash
matlab -batch "run_back('benchmarks/standard/pme/propeller/backmapping.json')"
```
