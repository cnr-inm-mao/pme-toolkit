function export_zenodo_regression(repo_root, output_path, solvers)
%EXPORT_ZENODO_REGRESSION Fit the complete published RAE2822 airfoil dataset.
% The package on the MATLAB path determines the implementation being tested.
% Pass "legacy" with the unchanged pre-snapshot package on the path.
arguments
    repo_root (1,1) string
    output_path (1,1) string
    solvers (1,:) string = ["auto", "direct", "snapshot"]
end

raw = load(fullfile(repo_root, 'databases', 'airfoil', 'database.mat'));
DB = raw.database;
assert(isequal(size(DB), [410, 16385]), 'Unexpected Zenodo airfoil database shape.');
results = struct();
fprintf('MATLAB fit source: %s\n', which('pme.fit'));
for mode = ["pme", "pi", "pd"]
    folder = mode;
    if mode ~= "pme", folder = mode + "_pme"; end
    casefile = fullfile(repo_root, 'benchmarks', 'standard', folder, 'airfoil', 'case.json');
    cfg = pme.read_case_json(casefile);
    layout = pme.parse_layout(cfg);
    [DB_used, ~, mask] = pme.filters(DB, cfg, layout);
    for solver = solvers
        cfg.solver = solver;
        fprintf('%s: fitting %s on all %d retained samples\n', upper(mode), solver, size(DB_used,2));
        started = tic;
        model = pme.fit(DB_used, cfg, layout);
        elapsed = toc(started);
        weights = model.W;
        if ~isvector(weights), weights = diag(weights); end
        nconf = model.sizes.nconf;
        if isfield(model.statsW, 'snapshot')
            info = model.statsW.snapshot;
            threshold = info.eigenvalue_threshold;
            total_variance = info.total_variance;
        else
            threshold = size(DB_used,2)*eps*max(model.L_full);
            total_variance = sum(real(model.L_full));
        end
        rank = max(nconf, sum(real(model.L_full) > threshold));
        entry = struct('values', real(model.L_full(1:rank)), ...
            'modes', model.Z_full(:,1:rank), ...
            'coordinates', model.ak_full(:,1:rank), ...
            'weights', weights, 'filter_mask', mask, 'nconf', nconf, ...
            'total_variance', total_variance, ...
            'achieved_ci', sum(real(model.Lr))/total_variance, ...
            'seconds', elapsed, 'kept_samples', size(DB_used,2));
        results.(char(mode)).(char(solver)) = entry;
        fprintf('%s %s: N=%d, variance=%.12f, elapsed=%.1fs\n', ...
            upper(mode), solver, nconf, entry.achieved_ci, elapsed);
    end
end
parent = fileparts(output_path);
if ~isempty(parent) && ~isfolder(parent), mkdir(parent); end
save(output_path, 'results', '-v7');
fprintf('Saved Zenodo regression results: %s\n', output_path);
end
