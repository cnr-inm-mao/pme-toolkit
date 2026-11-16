function [nconf, info] = choose_nconf(L, CI, total_variance, cluster_rtol, cluster_atol)
%PME.CHOOSE_NCONF Select variance retention without splitting a mode cluster.
% The optional denominator is the complete Gram trace before rank cutoff.
if nargin < 3 || isempty(total_variance), total_variance = sum(L); end
if nargin < 4, cluster_rtol = 1e-10; end
if nargin < 5, cluster_atol = 0; end
validateattributes(L, {'numeric'}, {'vector','real','finite','positive','nonempty'});
validateattributes(CI, {'numeric'}, {'scalar','real','finite','positive','<=',1});
validateattributes(total_variance, {'numeric'}, {'scalar','real','finite','positive'});
validateattributes(cluster_rtol, {'numeric'}, {'scalar','real','finite','nonnegative'});
validateattributes(cluster_atol, {'numeric'}, {'scalar','real','finite','nonnegative'});
L = L(:);
ratio = cumsum(L) / total_variance;
nconf = find(ratio >= CI - 10*eps, 1, 'first');
if isempty(nconf), nconf = numel(L); end
while nconf < numel(L)
    gap = abs(L(nconf) - L(nconf + 1));
    tolerance = max(cluster_atol, cluster_rtol * max(L(nconf), L(nconf + 1)));
    if gap > tolerance, break; end
    nconf = nconf + 1;
end
info = struct('achieved_ci', ratio(nconf), ...
    'resolved_variance_fraction', ratio(end), 'ci_met', ratio(nconf) >= CI - 10*eps);
if ~info.ci_met
    warning('pme:SnapshotVarianceTarget', ...
        ['Requested CI=%.16g exceeds the resolved variance fraction %.16g; ' ...
         'retaining all %d resolved modes.'], CI, ratio(end), numel(L));
end
end
