disp("Running PME-toolkit MATLAB tests")

this_file = mfilename('fullpath');
matlab_tests_dir = fileparts(this_file);
tests_root = fileparts(matlab_tests_dir);
repo_root = fileparts(tests_root);

addpath(genpath(repo_root))

rng(1)

test_config_loader
test_configuration_parity
test_physics_config
test_snapshot_decompose
test_snapshot_fit
test_streaming
test_run_case
test_io_controls
test_backmapping
test_regression

disp("All MATLAB tests passed")
