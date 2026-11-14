# Regression on the Zenodo airfoil dataset

The release regression uses the complete **RAE2822 airfoil** benchmark from
[Zenodo record 18958555](https://zenodo.org/records/18958555),
DOI `10.5281/zenodo.18958555`. The database has **410 rows and 16,385 columns**:
258 geometry coordinates, 20 native variables, 129 pressure coefficients and
three scalar responses. No columns are subsampled for this regression.

The SHA256 of the extracted `database.mat` is:

```text
a662f691c90158503ad627d1e4c36edafe566ec2fedb2ef3cadaacbb509cc177
```

The scripts verify both the checksum and the database shape before fitting.
They use the existing `benchmarks/standard/*/airfoil/case.json` files and their
configured filters. Removing columns with nonfinite data leaves **8,516**
samples. PME uses these samples. The additional standard IQR filter leaves
**7,391** samples for PI-PME and PD-PME. The baseline remains in each case.

## Comparisons

The unchanged pre-snapshot implementation is taken from commit
[`68309805`](https://github.com/cnr-inm-mao/pme-toolkit/commit/68309805e9aff5a9b877c33982c7181d8faa550b).
It runs in a separate package namespace in Python and a separate MATLAB
process. The Python regression verifies its source files against that commit.
The current version runs with each of `solver="auto"`, `solver="direct"` and
`solver="snapshot"`. The complete filtered dataset is used even when the
snapshot solver is explicitly selected.

Each comparison checks:

- Identical filter masks, weights and retained dimension at `CI=0.95`.
- Retained eigenvalues, and the resolved positive spectrum with errors scaled
  by the leading eigenvalue. Unresolved null modes are excluded from the
  spectral comparison.
- Explained variance divided by the complete weighted trace.
- Retained observation modes in the weighted norm, after sign alignment for
  isolated eigenvalues. Repeated eigenvalues are compared through their
  invariant subspace projector, since the individual eigenvectors may rotate.
- Native-variable mode components and the reconstructed native training data.
- An independent symmetric observation-covariance eigensolve, separate from
  both the original implementation and the current solver dispatch.

The eigenvector comparison concerns the retained basis used by the reduced
model. It does not require eigenvectors associated with numerical null modes
to agree. Native reconstruction is compared between implementations; this is
not a claim that truncating at 95% observation variance recovers every native
variable exactly.

The acceptance limits are `5e-9` for the maximum retained-eigenvalue relative
error and the leading-eigenvalue-scaled spectrum error, `5e-7` for the weighted
projector, sign-aligned retained modes and relative native-reconstruction
errors, and `5e-10` for the absolute explained-variance difference.

## Recorded Python results

The initial full-dataset snapshot regression was run on candidate
[`b36723d`](https://github.com/cnr-inm-mao/pme-toolkit/commit/b36723d9400a08668c4b88db7f9de143cf5d7767).
The following values compare that snapshot implementation with the unchanged
pre-snapshot implementation:

| Method | Samples retained by filters | Retained modes | Explained variance | Maximum retained eigenvalue relative error | Maximum sign-aligned weighted mode error |
|---|---:|---:|---:|---:|---:|
| PME | 8,516 | 5 | 95.1777828647% | 1.84e-15 | 5.05e-15 |
| PI-PME | 7,391 | 7 | 96.2809447954% | 4.28e-15 | 2.76e-14 |
| PD-PME | 7,391 | 6 | 95.8627977450% | 5.10e-15 | 2.14e-14 |

The resolved positive ranks were 126, 231 and 107, respectively. The maximum
absolute difference over the resolved spectrum, divided by the leading
eigenvalue, was `5.13e-16`, `1.39e-15` and `3.42e-15`. The absolute explained
variance differences were at most `8.89e-16`; relative native-reconstruction
differences were at most `1.64e-14`.

The subsequent local `auto` and `direct` runs also passed for all three
methods, with identical retained dimensions and explained variances. The
largest retained-eigenvalue relative error was `4.56e-15`, and the largest
weighted retained-mode error was `1.79e-14`.

With two BLAS threads in the local environment, the three forced-snapshot fits
took 74.2, 45.9 and 46.8 seconds. Direct fits took 0.16–0.36 seconds. These
measurements describe this dataset and environment, not a general performance
guarantee. There are many more retained samples than weighted observation
rows, so `auto` chooses `direct` for this dataset. Snapshot is advantageous in
the opposite regime.

## Reproduce and verify the release candidate

Create a checkout of the unchanged reference without modifying its files:

```bash
git worktree add --detach ../pme-legacy 68309805e9aff5a9b877c33982c7181d8faa550b
python -m pip install -e ./python
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
  python tests/python/zenodo_snapshot_regression.py \
  --legacy-root ../pme-legacy \
  --output results/airfoil_regression.json
```

The script downloads the archived Zenodo database if necessary. Its JSON
report records the repository commit, whether the source directory contains
uncommitted changes, source-file checksums, dataset checksum, filter counts,
spectra and numerical comparison errors. It does not store machine-specific
input paths.

The [Zenodo snapshot regression workflow](https://github.com/cnr-inm-mao/pme-toolkit/actions/workflows/zenodo-regression.yml)
runs the unchanged and current MATLAB implementations, then compares their
outputs against both Python implementations. Its `airfoil-regression`
artifact contains the JSON comparison report and both MATLAB output files.
The workflow must pass on the final release candidate before merging. The
local Python measurements above do not substitute for that MATLAB and
cross-language gate.
