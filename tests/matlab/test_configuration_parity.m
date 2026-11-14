function test_configuration_parity()
% Check canonical JSON defaults, baseline indices, filtering and orientation.
disp("Running configuration parity tests")
temporary = string(tempname);
mkdir(temporary);
cleanup = onCleanup(@() rmdir(temporary, 's')); %#ok<NASGU>
casefile = fullfile(temporary, 'case.json');
dbfile = fullfile(temporary, 'database.mat');
cfg = struct('mode', 'pme', ...
    'geom', struct('Jdir', 2, 'patches', struct('name', 'surface', 'K', 1)), ...
    'vars', struct('Mbase', 1, 'idx_active', []), ...
    'io', struct('dbfile', 'database.mat', 'outdir', 'results', 'save_model', false), ...
    'report', struct('enable', false));
database = [-1 1 -1 1; -.2 -.2 .2 .2; -2 -1 1 2]; %#ok<NASGU>
save(dbfile, 'database');
write_case(casefile, cfg);
out = pme.run_case(casefile);
model = out.model;
assert(model.cfg.CI == .99);
assert(strcmp(model.cfg.solver, 'auto'));
assert(model.sizes.nconf == 2);
assert(model.cfg.baseline_col == 1);
assert(strcmp(model.Uinfo.Urange_source, 'db'));
assert(isequal(model.Uinfo.Urange, [-2 2]));
assert(norm(model.P0 - [-1; -.2; 0], inf) < 1e-14);

% JSON baseline_col=1 refers to the second sample, including fixed variables.
cfg.baseline_col = 1;
cfg.vars = struct('Mbase', 2, 'idx_active', 0);
database = [-1 1 -1 1; -.2 -.2 .2 .2; -2 -1 1 2; 10 20 30 40]; %#ok<NASGU>
save(dbfile, 'database');
write_case(casefile, cfg);
out = pme.run_case(casefile);
assert(out.model.cfg.baseline_col == 2);
assert(norm(out.model.P0 - [1; -.2; .25], inf) < 1e-14);
assert(isequal(out.model.Uinfo.Ubase_baseline_raw, [-1; 20]));

% An earlier NaN and a goal filter must not shift the selected baseline.
cfg.mode = 'pi';
cfg.baseline_col = 3;
cfg.phys = struct('fields', [], 'scalars', struct('name', 'response', 'nCond', 1));
cfg.filters = struct('remove_nan', true, 'goal', struct('enable', true, ...
    'baseline_col', 3, 'metrics', struct('c_offset', 0, 'rule', 'leq_baseline', 'factor', .9)));
original = [NaN 1 2 3 4 5; 0 1 -1 .5 2 -2; ...
    0 10 20 30 40 50; 100 110 120 130 140 150; 0 2 7 5 8 3];
for orientation = ["never", "auto", "always"]
    cfg.io.transpose_if = char(orientation);
    if orientation == "never"
        database = original;
    else
        database = original';
    end
    save(dbfile, 'database');
    write_case(casefile, cfg);
    out = pme.run_case(casefile);
    assert(isequaln(out.DB, original));
    assert(isequal(out.model.filterMask, logical([0 1 0 1 0 1])));
    assert(out.model.cfg.baseline_col == 2);
    assert(norm(out.model.P0 - [3; .5; .5; 5], inf) < 1e-14);
    assert(isequal(out.model.Uinfo.Ubase_baseline_raw, [30; 130]));
    assert(out.meta.transposed == (orientation ~= "never"));
end

% Direct fitting with its optional filtering uses the same remapped index.
parsed = pme.read_case_json(casefile);
layout = pme.parse_layout(parsed);
direct = pme.fit(original, parsed, layout, 'apply_filters', true);
assert(norm(direct.P0 - out.model.P0, inf) < 1e-14);
assert(isequal(direct.Uinfo.Ubase_baseline_raw, [30; 130]));
disp("Configuration parity tests passed")
end

function write_case(path, cfg)
fid = fopen(path, 'w');
assert(fid ~= -1);
cleanup = onCleanup(@() fclose(fid)); %#ok<NASGU>
fprintf(fid, '%s', jsonencode(cfg));
end
