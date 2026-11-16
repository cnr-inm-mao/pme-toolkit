function result = decompose(Pc, w, options, solver)
%PME.DECOMPOSE Select the direct or snapshot weighted eigensolve.
%   solver is 'auto' (default), 'direct', or 'snapshot'. Auto solves the
%   smaller problem: the positive-weight observation covariance when it
%   has fewer rows than samples, otherwise the sample Gram matrix.

if nargin < 3, options = struct(); end
if nargin < 4, solver = 'auto'; end
if ~((ischar(solver) && isrow(solver)) || (isstring(solver) && isscalar(solver)))
    error('pme:Solver', 'solver must be auto, direct, or snapshot.');
end
requested = lower(string(solver));
if ~any(requested == ["auto", "direct", "snapshot"])
    error('pme:Solver', 'solver must be auto, direct, or snapshot.');
end
chosen = requested;
if chosen == "auto"
    if nnz(w > 0) < size(Pc, 2)
        chosen = "direct";
    else
        chosen = "snapshot";
    end
end
if chosen == "direct"
    result = pme.direct_decompose(Pc, w, options);
else
    result = pme.snapshot_decompose(Pc, w, options);
end
result.info.solver = char(chosen);
result.info.solver_requested = char(requested);
end
