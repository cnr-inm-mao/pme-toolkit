function test_regression()

disp("Running regression test")

this_file = mfilename('fullpath');
matlab_tests_dir = fileparts(this_file);
tests_root = fileparts(matlab_tests_dir);

results_dir = fullfile(tests_root, "cases", "results");
report_file = fullfile(results_dir, "report.mat");
model_file  = fullfile(results_dir, "model.mat");

assert(isfile(report_file), "Missing report file: %s", report_file)
assert(isfile(model_file),  "Missing model file: %s", model_file)

Srep = load(report_file);
assert(isfield(Srep, "rep"), "Missing variable 'rep' in report.mat")
assert(isstruct(Srep.rep), "Variable 'rep' is not a struct")
assert(isfield(Srep.rep, "nconf"), "Field 'nconf' not found in report struct")

nconf_expected = 10;
nconf = Srep.rep.nconf;

assert(nconf == nconf_expected, ...
    "Regression failed: expected nconf=%d, got %d", nconf_expected, nconf)

Smodel = load(model_file);
assert(isfield(Smodel, "model"), "Missing variable 'model' in model.mat")
assert(isstruct(Smodel.model), "Variable 'model' is not a struct")

model = Smodel.model;

assert(isfield(model, "Lr"), "Field 'Lr' not found in model struct")
assert(isfield(model, "Zr"), "Field 'Zr' not found in model struct")

% --- WRITE MATLAB REFERENCE FOR PYTHON ALIGNMENT ---

ref_dir = fullfile(tests_root, "reference");
if ~isfolder(ref_dir)
    mkdir(ref_dir);
end

ref_file = fullfile(ref_dir, "matlab_glider_reference.mat");

Lr = model.Lr;   %#ok<NASGU>
Zr = model.Zr;   %#ok<NASGU>

save(ref_file, "nconf", "Lr", "Zr", "-v7");

disp("Saved MATLAB reference to:")
disp(ref_file)

disp("Regression test passed")

end
