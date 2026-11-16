function test_io_controls()
% The public wrapper must preserve the case runner's persistence setting.

disp("Running model persistence tests")
original_dir = pwd;
folder = string(tempname);
mkdir(folder);
cleanup = onCleanup(@() cleanup_folder(folder, original_dir)); %#ok<NASGU>
t = linspace(0, 1, 8);
database = [t; t.^2; t]; %#ok<NASGU>
save(fullfile(folder, 'database.mat'), 'database');
cfg = struct('mode', "pme", 'CI', 0.95, 'baseline_col', 0, ...
    'geom', struct('Jdir', 2, 'patches', struct('K', 1)), ...
    'vars', struct('Mbase', 1, 'idx_active', [], 'use_db_range_if_missing', true), ...
    'filters', struct('remove_nan', true), 'report', struct('enable', false));
casefile = fullfile(folder, 'case.json');

for choice = 1:3
    % Explicit true, explicit false, and omitted (default true).
    cfg.io = struct('dbfile', "database.mat", 'transpose_if', "never", ...
        'outdir', sprintf('results_%d', choice));
    if choice < 3, cfg.io.save_model = (choice == 1); end
    write_case(casefile, cfg);
    out = run_pme(casefile);
    expected = choice ~= 2;
    assert(out.saved.model == expected, 'Unexpected model persistence status');
    assert(isfile(fullfile(out.outdir, 'model.mat')) == expected, ...
        'run_pme must honor io.save_model');
    assert(out.model.sizes.nconf > 0, 'The in-memory model must remain available');
end

% Disabling writes must leave a pre-existing model file untouched.
cfg.io.outdir = 'results_1';
cfg.io.save_model = false;
model_file = fullfile(folder, 'results_1', 'model.mat');
sentinel = 123; %#ok<NASGU>
save(model_file, 'sentinel');
write_case(casefile, cfg);
out = run_pme(casefile);
saved = load(model_file);
assert(~out.saved.model && isfield(saved, 'sentinel') && saved.sentinel == 123, ...
    'Disabled persistence must not overwrite or remove an existing model');

% An omitted output directory is shared by fitting and backmapping. A
% same-named directory in the working directory must not capture the lookup.
cfg.io = struct('dbfile', "database.mat", 'transpose_if', "never");
write_case(casefile, cfg);
fitted = run_pme(casefile);
backfile = fullfile(folder, 'backmapping.json');
back_cfg = struct('case_json', "case.json", ...
    'output', struct('file', "results/recovered.txt", 'what', "Ubase"));
write_case(backfile, back_cfg);
other_dir = fullfile(folder, 'unrelated');
mkdir(fullfile(other_dir, 'results'));
cd(other_dir);
recovered = pme.backmapping(backfile, ...
    'x01', 0.5 * ones(fitted.model.sizes.nconf, 1));
assert(string(recovered.outdir) == fullfile(folder, 'results'));
assert(string(recovered.model_file) == fullfile(folder, 'results', 'model.mat'));
assert(isfile(fullfile(folder, 'results', 'recovered.txt')));
assert(~isfile(fullfile(other_dir, 'results', 'model.mat')));
assert(norm(recovered.U - mean(t)) < 1e-12, 'Unexpected native mean reconstruction');
cd(original_dir);
disp("Model persistence tests passed")
end

function write_case(path, cfg)
fid = fopen(path, 'w');
assert(fid ~= -1, 'Could not create temporary case file');
cleanup = onCleanup(@() fclose(fid)); %#ok<NASGU>
fprintf(fid, '%s', jsonencode(cfg));
end

function cleanup_folder(folder, original_dir)
cd(original_dir);
rmdir(folder, 's');
end
