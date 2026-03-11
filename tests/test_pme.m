function test_pme()

disp("Running PME test")

this_file = mfilename('fullpath');
tests_dir = fileparts(this_file);

casefile = fullfile(tests_dir, "cases", "test_glider.json");
results_dir = fullfile(tests_dir, "results");

if ~isfolder(results_dir)
    mkdir(results_dir);
end

out = pme.run_case(string(casefile));

assert(~isempty(out), "PME run failed")
assert(isstruct(out), "PME output is not a struct")
assert(isfield(out, "model"), "PME output does not contain field 'model'")

model = out.model; %#ok<NASGU>
save(fullfile(results_dir, "model.mat"), "model")

disp("PME test passed")

end
