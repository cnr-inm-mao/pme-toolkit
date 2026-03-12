function test_backmapping()

disp("Running backmapping test")

this_file = mfilename('fullpath');
matlab_tests_dir = fileparts(this_file);
tests_root = fileparts(matlab_tests_dir);

casefile = fullfile(tests_root, "cases", "test_glider_back.json");
results_dir = fullfile(matlab_tests_dir, "results");
model_file = fullfile(results_dir, "model.mat");
output_file = fullfile(results_dir, "u_base.txt");

x01 = [0.1; 0.7; 0.3; 0.9; 0.2];

out = pme.backmapping(string(casefile), ...
    "x01", x01, ...
    "model_file", model_file, ...
    "output_file", output_file);

assert(~isempty(out), "Empty output from pme.backmapping")
assert(isfile(output_file), "Backmapping output file not found: %s", output_file)

disp("Backmapping test passed")

end