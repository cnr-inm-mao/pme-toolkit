function out = run_pme(casefile, outdir)
%RUN_PME Thin wrapper for JSON-driven PME benchmark execution.
%
%   OUT = RUN_PME(CASEFILE)
%   OUT = RUN_PME(CASEFILE, OUTDIR)
%
% Runs pme.run_case on the given JSON case and saves model.mat alongside
% report.mat for subsequent MATLAB backmapping workflows.

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

    assert(isstruct(out), "run_pme output is not a struct")
    assert(isfield(out, "model"), "run_pme output does not contain field 'model'")
    assert(isfield(out, "outdir"), "run_pme output does not contain field 'outdir'")

    model = out.model; %#ok<NASGU>

    outdir_final = string(out.outdir);
    model_path = fullfile(outdir_final, "model.mat");
    save(model_path, "model", "-v7");

    fprintf("[run_pme] wrote %s\n", model_path);

end
