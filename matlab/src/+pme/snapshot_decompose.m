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
opts = pme.decomposition_options(options, S);
block_rows = opts.block_rows;

K = zeros(S, S);
for first = 1:block_rows:R
    rows = first:min(first + block_rows - 1, R);
    block = sqrt(w(rows)) .* (Pc(rows, :) / sqrt(S));
    K = K + block' * block;
end
[A, lambda, info] = pme.resolved_eigensystem(K, S, options);

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
result.info = info;
result.info.solver = 'snapshot';
result.info.solver_requested = 'snapshot';
end
