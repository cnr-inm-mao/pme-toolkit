function model = fit_streaming(reader, shape, weights, native, options, ci, mode_writer)
%PME.FIT_STREAMING Fit snapshot PME from replayable observation row blocks.
%   model = pme.fit_streaming(reader, [Q,S], weights, native, options, ci)
%   reads raw Q-by-S observations through reader(first,last), using 1-based
%   inclusive row bounds. Weights is a Q-vector or a matching block reader.
%   Weights must already include the fixed normalization for entire sources.
%   Native is M-by-S paired data, in the coordinates required for backmapping.
%
%   The default result stores only native modes and the sample-space factors.
%   It does not retain the observation matrix, modes, means, or reader. If
%   mode_writer is supplied, a second pass calls
%       mode_writer(first,last,observation_modes)
%   for each block. Construction and query readers must preserve row and
%   sample ordering. See pme.transform_streaming for encoding new observations.

if nargin < 5 || isempty(options), options = struct(); end
if nargin < 6 || isempty(ci), ci = 0.95; end
if nargin < 7, mode_writer = []; end
validateattributes(shape, {'numeric'}, {'vector','numel',2,'real','integer','positive','finite'});
shape = double(shape(:)');
Q = shape(1); S = shape(2);
if S < 2
    error('pme:SnapshotSamples', 'Snapshot fitting requires at least two samples.');
end
if ~isa(reader, 'function_handle')
    error('pme:StreamingReader', 'The observation reader must be a function handle.');
end
if ~isempty(mode_writer) && ~isa(mode_writer, 'function_handle')
    error('pme:StreamingWriter', 'mode_writer must be a function handle.');
end
if ~isnumeric(native) || ~isreal(native) || ~ismatrix(native) || ...
        size(native,1) < 1 || size(native,2) ~= S || any(~isfinite(native(:)))
    error('pme:StreamingNative', 'Native data must be a finite real M-by-S matrix paired with the observations.');
end
validateattributes(ci, {'numeric'}, {'scalar','real','finite','positive','<=',1});
opts = pme.decomposition_options(options, S);
K = zeros(S, S);
for first = 1:opts.block_rows:Q
    last = min(first + opts.block_rows - 1, Q);
    block = pme.read_observation_block(reader, first, last, S);
    delta = block - block(:,1);
    centered = delta - mean(delta, 2);
    w = pme.read_weight_block(weights, first, last, Q);
    scaled = sqrt(w) .* (centered / sqrt(S));
    K = K + scaled' * scaled;
end
[A, lambda, info] = pme.resolved_eigensystem(K, S, options);
[nconf, selection] = pme.choose_nconf(lambda, ci, info.total_variance, ...
    info.cluster_rtol, info.eigenvalue_threshold);
A = A(:,1:nconf);
for k = 1:nconf
    [~, pivot] = max(abs(A(:,k)));
    if A(pivot,k) < 0, A(:,k) = -A(:,k); end
end
scales = sqrt(S) * sqrt(lambda(1:nconf)');
lifting = A ./ scales;
native = double(native);
native_delta = native - native(:,1);
native_delta_mean = mean(native_delta,2);
native_mean = native(:,1) + native_delta_mean;
native_modes = (native_delta - native_delta_mean) * lifting;
coordinates = A .* scales;
if any(~isfinite(native_modes(:))) || any(~isfinite(coordinates(:)))
    error('pme:SnapshotOverflow', 'Snapshot mode lifting produced nonfinite values.');
end
fields = fieldnames(selection);
for k = 1:numel(fields), info.(fields{k}) = selection.(fields{k}); end
info.solver = 'snapshot';
info.solver_requested = 'snapshot';
info.observation_passes = 1 + ~isempty(mode_writer);
model = struct('shape', shape, 'eigenvalues', lambda, 'sample_vectors', A, ...
    'lifting', lifting, 'coordinates', coordinates, 'native_mean', native_mean, ...
    'native_modes', native_modes, 'nconf', nconf, 'info', info);
if ~isempty(mode_writer)
    for first = 1:opts.block_rows:Q
        last = min(first + opts.block_rows - 1, Q);
        block = pme.read_observation_block(reader, first, last, S);
        delta = block - block(:,1);
        modes = (delta - mean(delta,2)) * lifting;
        if any(~isfinite(modes(:)))
            error('pme:SnapshotOverflow', 'Observation mode lifting produced nonfinite values.');
        end
        mode_writer(first, last, modes);
    end
end
end
