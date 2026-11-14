function parsed = decomposition_options(options, S)
%PME.DECOMPOSITION_OPTIONS Validate shared eigensolver tolerances.
if nargin < 1 || isempty(options), options = struct(); end
if ~isstruct(options) || ~isscalar(options)
    error('pme:SnapshotOptions', 'snapshot options must be a scalar struct.');
end
requested = option_value(options, 'eig_rtol', S*eps);
parsed = struct('eig_rtol', max(requested, S*eps), ...
    'eig_rtol_requested', requested, ...
    'eig_atol', option_value(options, 'eig_atol', 0), ...
    'cluster_rtol', option_value(options, 'cluster_rtol', 1e-10), ...
    'block_rows', option_value(options, 'block_rows', 4096));
if parsed.block_rows < 1 || parsed.block_rows ~= floor(parsed.block_rows)
    error('pme:SnapshotOptions', 'snapshot.block_rows must be a positive integer.');
end
end

function value = option_value(options, name, fallback)
if isfield(options, name), value = options.(name); else, value = fallback; end
if ~isnumeric(value) || ~isreal(value) || ~isscalar(value) || ~isfinite(value) || value < 0
    error('pme:SnapshotOptions', 'snapshot.%s must be a finite nonnegative scalar.', name);
end
value = double(value);
end
