function [vectors, lambda, info] = resolved_eigensystem(matrix, S, options)
%PME.RESOLVED_EIGENSYSTEM Positive modes of a symmetric weighted matrix.
%   S is the construction sample count for the shared numerical-rank floor.
opts = pme.decomposition_options(options, S);
if any(~isfinite(matrix(:)))
    error('pme:SnapshotOverflow', 'The weighted eigenproblem is not finite.');
end
matrix = 0.5*matrix + 0.5*matrix';
total_variance = trace(matrix);
if ~isfinite(total_variance)
    error('pme:SnapshotOverflow', 'The total weighted variance is not finite.');
end
[vectors, lambda] = eig(matrix, 'vector');
[lambda, order] = sort(real(lambda), 'descend');
vectors = real(vectors(:, order));
negative_tolerance = 100*S*eps*max(abs(lambda));
if any(lambda < -negative_tolerance)
    error('pme:SnapshotIndefinite', 'The weighted eigenproblem has significantly negative eigenvalues.');
end
threshold = max(opts.eig_atol, opts.eig_rtol * max(lambda(1), 0));
resolved = lambda > threshold;
if total_variance <= 0 || ~any(resolved)
    error('pme:SnapshotRank', 'No resolved positive weighted variance remains at the requested tolerances.');
end
lambda = lambda(resolved);
vectors = vectors(:, resolved);
info = opts;
info.total_variance = total_variance;
info.numerical_rank = numel(lambda);
info.eigenvalue_threshold = threshold;
info.matrix_dimension = size(matrix,1);
end
