function test_snapshot_decompose()
% Positive-spectrum equivalence, native lifting, and numerical rank policy.
disp("Running snapshot decomposition tests")
saved_rng = rng;
cleanup_rng = onCleanup(@() rng(saved_rng)); %#ok<NASGU>
rng(824)
Q = 20; S = 12; M = 3;
lambda = [4; 1; 1; 0.1; 1e-7];
rank_exact = numel(lambda);
samples = randn(S, rank_exact);
samples = samples - mean(samples, 1);
[A, ~] = qr(samples, 0);
[Y, ~] = qr(randn(Q, rank_exact), 0);
w_obs = linspace(0.25, 3, Q)';
H = (Y ./ sqrt(w_obs)) * diag(sqrt(S * lambda)) * A';
U = randn(M, S);
U = U - mean(U, 2);
P = [H; U];
w = [w_obs; zeros(M, 1)];
options = struct('eig_rtol', 1e-12, 'block_rows', 3);
out = pme.snapshot_decompose(P, w, options);

assert(numel(out.eigenvalues) == rank_exact, 'Null modes were retained.');
assert(norm(out.eigenvalues-lambda, inf) < 2e-13);
assert(norm(out.modes'*(w.*out.modes)-eye(rank_exact), 'fro') < 1e-7);
assert(norm(out.coordinates-P'*(w.*out.modes), 'fro') < 1e-8);
native_hat = out.modes(Q+1:end,:) * out.coordinates';
assert(norm(native_hat-U*(out.sample_vectors*out.sample_vectors'), 'fro') < 1e-11);

% Independent symmetric direct solve with native recovery from its equation.
B = sqrt(w_obs) .* H;
[direct_Y, direct_lambda] = eig((B*B')/S, 'vector');
[direct_lambda, order] = sort(direct_lambda, 'descend');
direct_lambda = direct_lambda(1:rank_exact);
direct_Z = direct_Y(:, order(1:rank_exact)) ./ sqrt(w_obs);
direct_V = (U*(H'*(w_obs.*direct_Z))) ./ (S*direct_lambda');
direct_X = H'*(w_obs.*direct_Z);
assert(norm(native_hat-direct_V*direct_X', 'fro') / norm(U,'fro') < 1e-7);

T = ((P*P')/S) .* w';
residual = T*out.modes - out.modes.*out.eigenvalues';
assert(norm(residual,'fro') / (norm(T,'fro')*norm(out.modes,'fro')) < 1e-12);

% Storage blocks and zero-weight rows must not change the observation metric.
one_block = pme.snapshot_decompose(P, w, struct('eig_rtol',1e-12,'block_rows',100));
assert(norm(out.eigenvalues-one_block.eigenvalues, inf) < 2e-13);
assert(norm(out.sample_vectors*out.sample_vectors' - ...
    one_block.sample_vectors*one_block.sample_vectors', 'fro') < 1e-7);
changed_native = pme.snapshot_decompose([H; 1e6*U], w, options);
assert(norm(out.eigenvalues-changed_native.eigenvalues, inf) < 2e-13);
assert(norm(out.sample_vectors*out.sample_vectors' - ...
    changed_native.sample_vectors*changed_native.sample_vectors', 'fro') < 1e-7);

% The target falls inside the repeated eigenvalue and must retain its cluster.
[nconf, selected] = pme.choose_nconf(out.eigenvalues, 0.7, ...
    out.info.total_variance, 1e-10, out.info.eigenvalue_threshold);
assert(nconf == 3 && selected.ci_met);

% Discarding a resolved tail cannot renormalize the remaining variance to 1.
cut = pme.snapshot_decompose(P, w, struct('eig_rtol',0.01));
assert(numel(cut.eigenvalues) == 4);
assert(abs(cut.info.total_variance-sum(lambda)) < 2e-13);
lastwarn('');
[nconf, selected] = pme.choose_nconf(cut.eigenvalues, 1, ...
    cut.info.total_variance, cut.info.cluster_rtol, cut.info.eigenvalue_threshold);
[~, warning_id] = lastwarn;
assert(nconf == 4 && ~selected.ci_met);
assert(strcmp(warning_id, 'pme:SnapshotVarianceTarget'));
assert(selected.achieved_ci < 1);

% S > R still returns only the observation rank, not native-only directions.
wide = pme.snapshot_decompose(P([1:2,Q+1:end],:), w([1:2,Q+1:end]), options);
assert(numel(wide.eigenvalues) == 2);

% A finite eigenvalue near realmax must not overflow during mode scaling.
large = pme.snapshot_decompose([1e154,-1e154], 1);
assert(all(isfinite(large.modes(:))) && all(isfinite(large.coordinates(:))));
assert(abs(large.eigenvalues/1e308-1) < 1e-13);
assert(norm((large.modes*large.coordinates')/1e154-[1,-1]) < 1e-13);

% Requested zero tolerances retain the numerical floor for a rank-one metric.
x = (0:7)-3.5;
unobserved = x.^2-mean(x.^2);
for requested_rtol = [0, 1e-300]
    rank_one = pme.snapshot_decompose([x;2*x;unobserved], [1;1;0], ...
        struct('eig_rtol',requested_rtol,'eig_atol',0));
    assert(numel(rank_one.eigenvalues)==1);
    assert(rank_one.info.eig_rtol==8*eps);
    assert(rank_one.info.eig_rtol_requested==requested_rtol);
    assert(norm(rank_one.modes(3,:)*rank_one.coordinates') < 1e-12);
end

assert_error(@() pme.snapshot_decompose(zeros(4,5), ones(4,1)), 'pme:SnapshotRank');
assert_error(@() pme.snapshot_decompose(P, zeros(size(w))), 'pme:SnapshotRank');
assert_error(@() pme.snapshot_decompose(P(:,1), w), 'pme:SnapshotSamples');
assert_error(@() pme.snapshot_decompose(P, w(2:end)), 'pme:SnapshotWeights');
assert_error(@() pme.snapshot_decompose(P, w, struct('eig_rtol',-1)), 'pme:SnapshotOptions');
assert_error(@() pme.snapshot_decompose(P, w, struct('block_rows',1.5)), 'pme:SnapshotOptions');
assert_error(@() pme.snapshot_decompose(P, w, struct('block_rows',0)), 'pme:SnapshotOptions');
assert_error(@() pme.snapshot_decompose(P, w, struct('eig_atol',Inf)), 'pme:SnapshotOptions');
assert_error(@() pme.snapshot_decompose(P, -ones(size(w))), '');
assert_error(@() pme.choose_nconf(lambda, 1.1), '');
disp("Snapshot decomposition tests passed")
end

function assert_error(action, expected)
try
    action();
catch err
    if ~isempty(expected)
        assert(strcmp(err.identifier, expected), ...
            'Expected %s, got %s: %s', expected, err.identifier, err.message);
    end
    return;
end
error('Expected an error, but the call succeeded.');
end
