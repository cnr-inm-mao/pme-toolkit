# Snapshot formulation

Version 1.3.0 computes PME, PI-PME and PD-PME using a symmetric eigenproblem in
sample space in both MATLAB and Python. This develops the Python implementation
contributed by Antoine DeBlois in
[pull request #1](https://github.com/cnr-inm-mao/pme-toolkit/pull/1).

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

## Storage and scope

The working storage is $O(RS+S^2)$, plus the returned modes, with at most
$O(bS)$ temporary weighted storage for a row-block size $b$. No dense
$R\times R$ covariance or weight matrix is allocated by the fitting path.
The main advantage is for many more observation rows than samples; a large
sample count still makes the dense $S\times S$ eigensolve expensive.

The production case loader and centered construction data remain in memory.
Row-block Gram assembly is not an out-of-core dataset loader. A streaming
observation provider, native-only model storage and cross-Gram query encoding
are not exposed by this release. Experiments from a separate research
implementation should not be attributed to the toolkit without rerunning
them on the released version.

See [Reproducibility](reproducibility.md) for the direct-reference tests and
the comparison of current MATLAB and Python results.
