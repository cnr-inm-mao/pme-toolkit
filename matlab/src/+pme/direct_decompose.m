function result = direct_decompose(Pc, w, options)
%PME.DIRECT_DECOMPOSE Symmetric direct solve on positive-weight rows.
%   The observation modes are unwhitened covariance eigenvectors. Rows
%   with zero weight, including native variables, are recovered from the
%   paired construction samples and do not enlarge the eigenproblem.

if nargin < 3 || isempty(options), options = struct(); end
validateattributes(Pc, {'numeric'}, {'2d','real','finite','nonempty'}, mfilename, 'Pc');
validateattributes(w, {'numeric'}, {'vector','real','finite','nonnegative'}, mfilename, 'w');
Pc = double(Pc);
w = double(w(:));
[R, S] = size(Pc);
if S < 2
    error('pme:SnapshotSamples', 'Weighted fitting requires at least two samples.');
end
if numel(w) ~= R
    error('pme:SnapshotWeights', 'The weight vector must have one entry per row of Pc.');
end
pme.decomposition_options(options, S);
active = w > 0;
if ~any(active)
    error('pme:SnapshotRank', 'No resolved positive weighted variance remains at the requested tolerances.');
end
B = sqrt(w(active)) .* (Pc(active, :) / sqrt(S));
C = B * B';
[Y, lambda, info] = pme.resolved_eigensystem(C, S, options);
A = (B' * Y) ./ sqrt(lambda');
scales = sqrt(S) * sqrt(lambda');
coordinates = A .* scales;
for k = 1:size(A, 2)
    [~, pivot] = max(abs(A(:, k)));
    if A(pivot, k) < 0
        A(:, k) = -A(:, k);
        Y(:, k) = -Y(:, k);
        coordinates(:, k) = -coordinates(:, k);
    end
end
modes = zeros(R, numel(lambda));
modes(active, :) = Y ./ sqrt(w(active));
modes(~active, :) = Pc(~active, :) * (A ./ scales);
if any(~isfinite(modes(:))) || any(~isfinite(coordinates(:)))
    error('pme:SnapshotOverflow', 'Weighted mode lifting produced nonfinite values.');
end
result = struct('eigenvalues', lambda, 'sample_vectors', A, ...
    'modes', modes, 'coordinates', coordinates);
result.info = info;
result.info.solver = 'direct';
result.info.solver_requested = 'direct';
end
