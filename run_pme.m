function out = run_pme(casefile)
%RUN_PME Thin wrapper for JSON-driven PME benchmark execution.
%
%   OUT = RUN_PME(CASEFILE) adds the MATLAB source tree to the path and
%   dispatches the case to pme.run_case.

    if nargin < 1 || strlength(string(casefile)) == 0
        casefile = "benchmarks/standard/pme/glider/case.json";
    end

    addpath(genpath("matlab/src"));
    out = pme.run_case(casefile);
end
