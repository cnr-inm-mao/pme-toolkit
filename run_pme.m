function out = run_pme(casefile, outdir)
%RUN_PME Thin wrapper for JSON-driven PME benchmark execution.
%
%   OUT = RUN_PME(CASEFILE)
%   OUT = RUN_PME(CASEFILE, OUTDIR)
%
% Runs pme.run_case on the given JSON case. Model persistence follows
% cfg.io.save_model (true by default); reporting follows cfg.report.enable.

    if nargin < 1 || strlength(string(casefile)) == 0
        casefile = "benchmarks/standard/pme/glider/case.json";
    end

    casefile = string(casefile);

    this_file = mfilename('fullpath');
    repo_root = fileparts(this_file);

    addpath(genpath(fullfile(repo_root, "matlab", "src")));

    if nargin < 2 || strlength(string(outdir)) == 0
        out = pme.run_case(casefile);
    else
        out = pme.run_case(casefile, "outdir", string(outdir));
    end

end
