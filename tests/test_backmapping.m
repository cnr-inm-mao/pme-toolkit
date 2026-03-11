function test_backmapping()

disp("Running backmapping test")

this_file = mfilename('fullpath');
tests_dir = fileparts(this_file);

casefile = fullfile(tests_dir, "cases", "test_glider_back.json");

x01 = [0.1; 0.7; 0.3; 0.9; 0.2];

out = pme.backmapping(string(casefile), "x01", x01);

assert(~isempty(out), "Empty output from pme.backmapping")

disp("Backmapping test passed")

end
