function out = run_back(casefile)
%RUN_BACK Thin wrapper for JSON-driven backmapping execution.
%
%   OUT = RUN_BACK(CASEFILE)

    if nargin < 1 || strlength(string(casefile)) == 0
        casefile = "benchmarks/standard/pme/glider/backmapping.json";
    end

    casefile = string(casefile);

    this_file = mfilename('fullpath');
    repo_root = fileparts(this_file);

    addpath(genpath(fullfile(repo_root, "matlab", "src")));

    try
        out = pme.backmapping(casefile);
    catch ME
        if contains(string(ME.message), "Model file not found")
            msg = sprintf([ ...
                "Backmapping requires a previously saved model.mat. ", ...
                "Run run_pme(...) first on the corresponding case.\n\n", ...
                "Original error:\n%s"], ...
                ME.message);
            error("run_back:MissingModel", "%s", msg);
        else
            rethrow(ME);
        end
    end

end
