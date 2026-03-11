disp("Running PME-toolkit tests")

% -------------------------------------------------------------------------
% Resolve repository root and add to path
% -------------------------------------------------------------------------
this_file = mfilename('fullpath');
tests_dir = fileparts(this_file);
repo_root = fileparts(tests_dir);

addpath(genpath(repo_root))

rng(1)

% -------------------------------------------------------------------------
% Run tests
% -------------------------------------------------------------------------
test_pme
test_backmapping
test_regression

disp("All tests passed")
