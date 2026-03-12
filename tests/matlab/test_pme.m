function test_pme()

disp("Running PME test")

this_file = mfilename('fullpath');
matlab_tests_dir = fileparts(this_file);
tests_root = fileparts(matlab_tests_dir);

casefile = fullfile(tests_root, "cases", "test_glider.json");
results_dir = fullfile(matlab_tests_dir, "results");

if ~isfolder(results_dir)
    mkdir(results_dir);
end

out = pme.run_case(string(casefile), "outdir", results_dir);

assert(~isempty(out), "PME run failed")
assert(isstruct(out), "PME output is not a struct")
assert(isfield(out, "model"), "PME output does not contain field 'model'")

model = out.model; %#ok<NASGU>
save(fullfile(results_dir, "model.mat"), "model")

assert(isfile(fullfile(results_dir, "report.mat")), ...
    "Report file not found: %s", fullfile(results_dir, "report.mat"))

disp("PME test passed")

end