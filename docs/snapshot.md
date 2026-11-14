# Snapshot formulation

Version 1.3.0 provides direct and snapshot symmetric eigensolvers for PME,
PI-PME and PD-PME in both MATLAB and Python. The snapshot solver develops the Python implementation
contributed by Antoine DeBlois in
[pull request #1](https://github.com/cnr-inm-mao/pme-toolkit/pull/1).

## Solver selection

The case configuration accepts `solver`:

| Value | Eigenproblem | When it is useful |
|---|---|---|
| `auto` (default) | Chooses the smaller symmetric problem | Normal case workflows |
| `snapshot` | Sample Gram matrix, $S\times S$ | More observation rows than construction samples |
| `direct` | Weighted observation covariance, $Q_+\times Q_+$ | Fewer positive-weight observation rows than construction samples |

Here $Q_+$ counts rows with positive metric weight; native rows do not increase
the direct eigenproblem. `auto` chooses direct when $Q_+<S$, otherwise snapshot.
For a matched numerical comparison, explicitly run both choices on the same data
and configuration. The selected solver, requested solver and matrix dimension
are recorded under the existing `stats_w["snapshot"]` / `statsW.snapshot`
diagnostics. The `snapshot` options object supplies the numerical tolerances
for both solvers.

The direct path solves $BB^\mathsf{T}/S$, with
$B=\operatorname{diag}(\sqrt{w_+})P_{c,+}$, and obtains the paired native modes
from its sample coefficients. It preserves the direct PME formulation without
reintroducing the old dense diagonal weights or nonsymmetric augmented operator.
The previous implementation remains available in version history and is used
as an independent regression baseline.

```json
{
  "solver": "auto",
  "snapshot": {
    "eig_rtol": 1e-12,
    "eig_atol": 0,
    "cluster_rtol": 1e-10,
    "block_rows": 2048
  }
}
```

## Data and metric

Let $P_c$ contain the centered construction samples as columns, with $R$ rows
and $S$ samples. The toolkit keeps its existing row ordering:

- PME: geometry and active native variables;
- PI-PME: geometry, active native variables, physical fields and scalars;
- PD-PME: active native variables, physical fields and scalars.

The vector $w$ contains the existing variance-normalized observation weights.
Native-variable rows have zero weight. The corresponding diagonal matrix is
never needed by the fitting path.

## Gram eigenproblem and lifting

The sample matrix is

$$
K = \frac{1}{S}P_c^\mathsf{T}\operatorname{diag}(w)P_c.
$$

Row scaling applies the weights. Contributions are accumulated in blocks of
at most `snapshot.block_rows` rows, using the same fixed weights in every
block. The completed matrix is symmetrized before its eigenproblem is solved.

For a unit sample eigenvector $a_k$ and a resolved positive eigenvalue
$\lambda_k$, the complete mode and construction coordinates are

$$
z_k = \frac{P_c a_k}{\sqrt{S\lambda_k}},
\qquad
x_k^\mathsf{T} = \sqrt{S\lambda_k}\,a_k.
$$

Lifting uses every data row, including native variables with zero metric
weight. The native part of the mode therefore preserves the analytical
backmap. No inverse or pseudoinverse of the semidefinite metric is required.
For a common retained sample basis $A$, the centered native reconstruction is
$UAA^\mathsf{T}$. This equals $U$ only when its row space lies in the retained
observation sample space. Keeping every resolved observation mode does not
guarantee exact recovery of unrelated native variation.

The existing `run_case`, transform and backmapping interfaces continue to use
the construction means, native scaling and variable bounds. The eigensolver
does not enforce bounds on newly chosen reduced coordinates.

## Numerical rank and retained variance

Only eigenvalues satisfying

$$
\lambda_k > \tau,
\qquad
\tau = \max(\tau_{\mathrm{abs}},\tau_{\mathrm{rel}}\lambda_1)
$$

are lifted. Defaults are `eig_atol = 0` and `eig_rtol = S * eps`.
The effective relative cutoff is at least `S * eps`, even when a smaller value
is requested; both values are recorded. This prevents lifting roundoff modes
when the configured tolerances are zero.
Negative eigenvalues larger than the roundoff allowance cause an error;
null or unresolved modes are omitted. A dataset with no resolved positive
weighted variance raises an explicit error.

The requested confidence index uses the complete constructed trace:

$$
\rho_N = \frac{\sum_{k=1}^{N}\lambda_k}{\operatorname{tr}(K)}.
$$

This denominator is not replaced by the sum of the eigenvalues left after
thresholding or by the count of information sources. Constant sources still
appear in the source metadata but contribute no variance. Mode selection keeps
the whole cluster intersecting the confidence threshold. If numerical rank
truncation prevents reaching the requested confidence, the fit warns and records
the achieved fraction.

The Gram construction squares the positive-spectrum condition number of the
weighted data. Small eigenvalues and their native modes can therefore lose
accuracy. Diagnostics record the absolute and relative cutoff, numerical rank,
cluster tolerance, total variance and achieved retention.

## Model compatibility

`model.W` in MATLAB and `model.w` in Python store a vector of diagonal weights
in newly fitted models. When adapting custom code, replace multiplication by
the former dense matrix with row scaling. `pme.weights` and Python
`build_weights` retain their explicit dense return for callers that request it;
the normal fit uses the diagonal-only builders. Python loading and MATLAB
transform/report functions also accept legacy dense diagonal model weights.

Full-spectrum arrays now contain only resolved positive modes. Their size is
the numerical rank, rather than the number of state rows or samples.
`lam_cum_ninf` remains a report compatibility alias for the trace-normalized
`retained_variance` values.

## Streamed observations and compact native models

The standard case loader keeps the database in memory. For observations stored
on disk or generated in blocks, both languages also expose `fit_streaming`,
`transform_streaming` and `backmap_streaming`. This path always uses the snapshot
eigenproblem and reads at most `block_rows` observation rows at a time.

The fitting inputs are a repeatable observation reader, the shape $(Q,S)$,
fixed effective weights, and paired native data with shape $(M,S)$. The native
array is supplied separately; do not append its rows to the observation reader.
For PME the reader supplies geometry; for PI-PME it supplies geometry, fields
and scalars; for PD-PME it supplies fields and scalars. Row ordering, sample IDs,
units and weights must remain identical on every pass.

Weights can be a vector or a reader. They must include any quadrature, source
balancing or variance normalization before fitting. A source variance can be
accumulated in a preliminary pass over that entire source. Normalizing each
storage block independently changes the metric and is not equivalent.

The reader returns raw observations. The fit subtracts construction means
rowwise, accumulates the complete Gram matrix, selects complete resolved
eigenspaces, and returns the selected sample coefficients, construction
coordinates and native modes. It does not retain the observation matrix, its
modes, its row means or the readers. Native scaling and active-variable selection
are the caller's responsibility in this lower-level interface; backmapping
returns the same native units that were supplied, without clipping.

### Python

Python readers use zero-based, half-open bounds. A reader backed by a NumPy
memory map can be used as follows:

```python
import numpy as np
from pme_toolkit import fit_streaming, transform_streaming, backmap_streaming

observations = np.load("observations.npy", mmap_mode="r")  # Q by S
native = np.load("native.npy")  # M by S, paired construction designs
weights = np.load("weights.npy", mmap_mode="r")  # Q effective weights
reader = lambda start, stop: observations[start:stop, :]

model = fit_streaming(
    reader, observations.shape, weights, native,
    {"block_rows": 2048, "eig_rtol": 1e-12}, ci=0.99,
)
construction_native = backmap_streaming(model, model["coordinates"])

queries = np.load("queries.npy", mmap_mode="r")  # same Q rows, T queries
query_reader = lambda start, stop: queries[start:stop, :]
coordinates = transform_streaming(
    model, reader, query_reader, queries.shape[1], weights,
)
query_native = backmap_streaming(model, coordinates)  # M by T
```

### MATLAB

MATLAB readers use one-based, inclusive bounds. With a caller-defined disk or
generator reader, the equivalent calls are:

```matlab
% reader(first,last) returns (last-first+1)-by-S raw observations.
% weights is a Q-vector or weights(first,last) returns matching row weights.
options = struct('block_rows', 2048, 'eig_rtol', 1e-12);
model = pme.fit_streaming(reader, [Q,S], weights, native, options, 0.99);
construction_native = pme.backmap_streaming(model, model.coordinates);
coordinates = pme.transform_streaming(model, reader, query_reader, T, weights);
query_native = pme.backmap_streaming(model, coordinates);  % M by T
```

Coordinates use one design per row in both implementations. Readers and native
inputs use one design per column. The compact model fields have the same names
in MATLAB and Python: `shape`, `eigenvalues`, `sample_vectors`, `lifting`,
`coordinates`, `native_mean`, `native_modes`, `nconf` and `info`.
`eigenvalues` contains the full resolved spectrum; the sample factors and native
modes contain the selected `nconf` columns.

### Optional observation modes and query projection

An optional `mode_writer(first,last,modes)` callback receives selected
observation modes in a second pass. In Python its bounds are instead
`(start,stop)` and half-open, as for the reader. The writer can store each block
on disk without accumulating a full $Q\times N$ array. `info.observation_passes`
records whether the fitting call used one or two passes.

When observation modes are omitted, new observations are encoded using a
cross-Gram product. For a query $g=h-\bar h$,

$$
k=\frac{1}{S}H^\mathsf{T}Wg,
\qquad
x_j=\sqrt{\frac{S}{\lambda_j}}\,a_j^\mathsf{T}k.
$$

`transform_streaming` rereads construction blocks and reconstructs their means;
it always uses those means to center the queries. The construction reader and
weights must be the same as in the fit. Encoding physical observations still
requires those observations to be available for the query. Choosing reduced
coordinates directly and applying the native backmap requires only the compact
model.

## Storage and scope

The resident snapshot fit uses $O(RS+S^2)$ working storage, plus the returned
modes, with $O(bS)$ temporary block storage. The direct fit instead uses the
$Q_+\times Q_+$ observation covariance. Neither solver builds a dense weight
matrix.

The streamed native fit uses $O(bS+S^2+MS+SN+MN)$ storage and retains no full
observation array. A caller-supplied weight vector adds $O(Q)$ storage; a weight
reader avoids it. An optional mode writer determines where the $Q\times N$
output is stored. Query encoding adds a $T\times S$ cross-Gram matrix and
blocks with at most $bT$ entries. A large sample count remains expensive because
the Gram matrix and its dense eigensolve still depend on $S$.

The controlled manuscript driver in `benchmarks/snapshot/verify_manuscript.py`
uses these public toolkit APIs for the prescribed spectrum, geometric
regeneration, conditioning checks and a native-only run with 1,048,576
coordinates. Its saved outputs identify the actual source files, environment
and input protocol; earlier results from separate research scripts are not
silently relabelled as toolkit results.

See [Reproducibility](reproducibility.md) for the direct-reference tests and
the comparison of current MATLAB and Python results.
