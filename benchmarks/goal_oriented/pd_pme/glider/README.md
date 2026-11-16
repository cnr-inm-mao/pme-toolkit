# Goal-oriented benchmark — PD-PME — glider

This case runs PD-PME on the glider dataset with the goal-oriented sample-selection settings in `case.json`.
The same JSON configuration is used by MATLAB and Python.

## Solver

The case explicitly sets `"solver": "auto"`. The fit selects the smaller
direct or snapshot eigenproblem. Use `"direct"` or `"snapshot"` to select
a solver explicitly; omitting the field also defaults to `"auto"`.
See the [solver documentation](../../../../docs/snapshot.md).

## Run

After [installation](../../../../docs/quickstart.md), run from the repository root:

```bash
pme-run benchmarks/goal_oriented/pd_pme/glider/case.json
```

or:

```bash
matlab -batch "run_pme('benchmarks/goal_oriented/pd_pme/glider/case.json')"
```

The [dataset metadata](../../../../databases/glider/dataset.json) describes
the external data. Missing dataset files are downloaded by the case runner.
Outputs are written to `io.outdir`, relative to the case directory.

To construct a backmapping request for this case, follow the
[backmapping configuration guide](../../../../docs/backmapping_config.md).
