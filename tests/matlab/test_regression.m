function test_regression()

disp("Running regression test")

this_file = mfilename('fullpath');
matlab_tests_dir = fileparts(this_file);

report_file = fullfile(matlab_tests_dir, "results", "report.mat");
assert(isfile(report_file), "Missing report file: %s", report_file)

S = load(report_file);

assert(isfield(S, "rep"), "Missing variable 'rep' in report.mat")
assert(isstruct(S.rep), "Variable 'rep' is not a struct")
assert(isfield(S.rep, "nconf"), "Field 'nconf' not found in report struct")

nconf_expected = 10;
nconf = S.rep.nconf;

assert(nconf == nconf_expected, ...
    "Regression failed: expected nconf=%d, got %d", nconf_expected, nconf)

disp("Regression test passed")

end
