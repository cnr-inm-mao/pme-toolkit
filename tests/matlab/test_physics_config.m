function test_physics_config()
% Regression for issue #4: PI/PD must not silently omit physical inputs.

disp("Running physics configuration tests")

casefile = string(tempname) + ".json";
cleanup = onCleanup(@() delete(casefile)); %#ok<NASGU>

base = struct('mode', "pme", 'CI', 0.95, ...
    'geom', struct('Jdir', 2, 'patches', struct('K', 1)), ...
    'vars', struct('Mbase', 1, 'idx_active', []));
db = [0, 1, 2, 3; 0, 0.2, 0.5, 0.9; 0, 0.2, 0.5, 1];

invalidPhysics = {'', ',"phys":null', ',"phys":[]', ',"phys":{}', ...
    ',"phys":{"fields":[],"scalars":[]}', ...
    ',"phys":{"fields":[]}', ',"phys":{"scalars":[]}', ...
    ',"phys":"invalid"'};

for mode = ["pi", "pd", "PI", "PD"]
    expected = sprintf(['mode=''%s'' requires at least one physical field or scalar in ' ...
        'cfg.phys.fields or cfg.phys.scalars. Use mode=''pme'' for geometry-only PME.'], ...
        lower(mode));
    for i = 1:numel(invalidPhysics)
        raw = sprintf('{"mode":"%s"%s}', mode, invalidPhysics{i});
        cfg = jsondecode(raw);
        cfg.geom = base.geom;
        cfg.vars = base.vars;
        assert_missing_physics(@() pme.fit(db, cfg), expected);

        % Invalid physical configuration must be reported before range-file I/O.
        cfg.vars.Urange_file = "missing-range-file-for-issue-4.mat";
        cfg.io.dbfile = "missing-database-for-issue-4.mat";
        write_case(casefile, jsonencode(cfg));
        assert_missing_physics(@() pme.read_case_json(casefile), expected);
        assert_missing_physics(@() pme.run_case(casefile), expected);
    end
end

% Standard PME, including its default mode, remains usable without physics.
for explicitMode = [true, false]
    cfg = base;
    if ~explicitMode, cfg = rmfield(cfg, 'mode'); end
    write_case(casefile, jsonencode(cfg));
    loaded = pme.read_case_json(casefile);
    model = pme.fit(db, loaded);
    assert(strcmpi(model.mode, "pme"), "Expected standard PME")
    assert(model.sizes.P_rows == 3, "Unexpected standard PME composition")
end

% Either physical source alone is valid; no geometry or physics is synthesized.
physics = { ...
    struct('scalars', struct('name', "coefficient", 'nCond', 1)), ...
    struct('fields', struct('name', "pressure", 'nCond', 1, 'disc', struct('K', 1)))};
for mode = ["pi", "pd", "PI", "PD"]
    for i = 1:numel(physics)
        cfg = base;
        cfg.mode = mode;
        cfg.phys = physics{i};
        write_case(casefile, jsonencode(cfg));
        loaded = pme.read_case_json(casefile);
        model = pme.fit([db; 1, 1.4, 1.8, 2.6], loaded);
        assert(strcmpi(model.mode, mode), "Mode was changed during fit")
        assert(model.statsW.ninfo.F + model.statsW.ninfo.C == 1, ...
            "The configured physical source was not included")
        assert(all(isfinite(model.L_full)), "Fit returned nonfinite eigenvalues")
    end
end

disp("Physics configuration tests passed")
end

function write_case(path, text)
fid = fopen(path, 'w');
assert(fid ~= -1, 'Could not create temporary case file');
cleanup = onCleanup(@() fclose(fid)); %#ok<NASGU>
fprintf(fid, '%s', text);
end

function assert_missing_physics(action, expected)
try
    action();
catch err
    assert(strcmp(err.identifier, 'pme:MissingPhysics'), ...
        'Expected pme:MissingPhysics, got %s: %s', err.identifier, err.message);
    assert(strcmp(err.message, expected), 'Unexpected missing-physics error message');
    return;
end
error('Expected pme:MissingPhysics, but the call succeeded');
end
