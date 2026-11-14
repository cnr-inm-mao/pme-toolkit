function result = snapshot_decompose(Pc, w, options)
%PME.SNAPSHOT_DECOMPOSE Weighted snapshot eigensolve for centered row data.
%   Pc is R-by-S and w is the nonnegative diagonal of the metric. Native
%   rows may have zero weight; their mode components use the same lift as
%   the observation rows. Only resolved positive modes are returned.
%
%   options: eig_rtol (default S*eps), eig_atol (0), cluster_rtol (1e-10),
%   and block_rows (4096). Row blocks bound the weighted temporary array;
%   Pc and the returned modes still reside in memory.

if nargin < 3 || isempty(options), options = struct(); end
validateattributes(Pc, {'numeric'}, {'2d','real','finite','nonempty'}, mfilename, 'Pc');
validateattributes(w, {'numeric'}, {'vector','real','finite','nonnegative'}, mfilename, 'w');
Pc = double(Pc);
w = double(w(:));
[R, S] = size(Pc);
if S < 2
    error('pme:SnapshotSamples', 'Snapshot fitting requires at least two samples.');
end
if numel(w) ~= R
    error('pme:SnapshotWeights', 'The weight vector must have one entry per row of Pc.');
end
if ~isstruct(options) || ~isscalar(options)
    error('pme:SnapshotOptions', 'snapshot options must be a scalar struct.');
end
eig_rtol_requested = option_value(options, 'eig_rtol', S*eps);
eig_rtol = max(eig_rtol_requested, S*eps);
eig_atol = option_value(options, 'eig_atol', 0);
cluster_rtol = option_value(options, 'cluster_rtol', 1e-10);
block_rows = option_value(options, 'block_rows', 4096);
if block_rows < 1 || block_rows ~= floor(block_rows)
    error('pme:SnapshotOptions', 'snapshot.block_rows must be a positive integer.');
end

K = zeros(S, S);
for first = 1:block_rows:R
    rows = first:min(first + block_rows - 1, R);
    block = Pc(rows, :);
    K = K + (block' * (w(rows) .* block)) / S;
end
K = 0.5*K + 0.5*K';
if any(~isfinite(K(:)))
    error('pme:SnapshotOverflow', 'The weighted snapshot Gram matrix is not finite.');
end
total_variance = trace(K);
if ~isfinite(total_variance)
    error('pme:SnapshotOverflow', 'The total weighted snapshot variance is not finite.');
end
[A, lambda] = eig(K, 'vector');
[lambda, order] = sort(real(lambda), 'descend');
A = real(A(:, order));
negative_tolerance = 100*S*eps*max(abs(lambda));
if any(lambda < -negative_tolerance)
    error('pme:SnapshotIndefinite', 'The weighted Gram matrix has significantly negative eigenvalues.');
end
threshold = max(eig_atol, eig_rtol * max(lambda(1), 0));
resolved = lambda > threshold;
if total_variance <= 0 || ~any(resolved)
    error('pme:SnapshotRank', 'No resolved positive weighted variance remains at the requested tolerances.');
end
lambda = lambda(resolved);
A = A(:, resolved);

% Fix signs without choosing a basis inside a repeated eigenspace.
for k = 1:size(A, 2)
    [~, pivot] = max(abs(A(:, k)));
    if A(pivot, k) < 0, A(:, k) = -A(:, k); end
end
scales = sqrt(S) * sqrt(lambda');
result = struct();
result.eigenvalues = lambda;
result.sample_vectors = A;
result.modes = Pc * (A ./ scales);
result.coordinates = A .* scales;
if any(~isfinite(result.modes(:))) || any(~isfinite(result.coordinates(:)))
    error('pme:SnapshotOverflow', 'Snapshot mode lifting produced nonfinite values.');
end
result.info = struct('total_variance', total_variance, ...
    'numerical_rank', numel(lambda), 'eig_rtol', eig_rtol, ...
    'eig_rtol_requested', eig_rtol_requested, ...
    'eig_atol', eig_atol, 'eigenvalue_threshold', threshold, ...
    'cluster_rtol', cluster_rtol, 'block_rows', block_rows);
end

function value = option_value(options, name, fallback)
if isfield(options, name)
    value = options.(name);
else
    value = fallback;
end
if ~isnumeric(value) || ~isreal(value) || ~isscalar(value) || ~isfinite(value) || value < 0
    error('pme:SnapshotOptions', 'snapshot.%s must be a finite nonnegative scalar.', name);
end
value = double(value);
end
