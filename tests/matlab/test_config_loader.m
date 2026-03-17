function test_config_loader()

disp("Running config loader test")

this_file = mfilename('fullpath');
matlab_tests_dir = fileparts(this_file);
tests_root = fileparts(matlab_tests_dir);
repo_root = fileparts(tests_root);

cfg_path = fullfile(repo_root, "benchmarks", "standard", "pme", "glider", "case.json");

cfg = pme.read_case_json(string(cfg_path));

assert(isstruct(cfg), "Config is not a struct")
assert(isfield(cfg, "mode"), "Missing field 'mode'")
assert(strcmpi(string(cfg.mode), "pme"), "Expected mode='pme'")
assert(isfield(cfg, "geom"), "Missing field 'geom'")
assert(isfield(cfg, "vars"), "Missing field 'vars'")
assert(isfield(cfg, "io"), "Missing field 'io'")
assert(isfield(cfg.io, "dbfile"), "Missing field 'io.dbfile'")
assert(isfile(cfg.io.dbfile), "Resolved dbfile does not exist: %s", cfg.io.dbfile)

disp("Config loader test passed")

end
