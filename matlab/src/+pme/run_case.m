function out = run_case(jsonFile)
%PME.RUN_CASE Run a complete PME case from a canonical JSON file.
%
% out = pme.run_case(".../case.json")
%
% Pipeline:
%   1) read JSON (canonical config)
%   2) parse layout
%   3) load DB
%   4) enforce orientation
%   5) apply filters ONCE (keeps mask)
%   6) fit model on DB_used (fit does NOT filter)
%   7) save model (optional)
%   8) report (optional: prints + plots + report.mat)
%
% Output:
% out.cfg, out.layout, out.meta, out.DB, out.DB_used, out.model, out.outdir, out.saved, out.rep

arguments
    jsonFile (1,1) string
end

% ----------------------------
% 0) Ensure external dataset exists
% ----------------------------
pme.ensure_case_inputs(jsonFile);

% ----------------------------
% 1) Read config + defaults
% ----------------------------
cfg = pme.read_case_json(jsonFile);

% Report defaults
if ~isfield(cfg,'report'), cfg.report = struct(); end
if ~isfield(cfg.report,'enable'), cfg.report.enable = true; end

% IO defaults
if ~isfield(cfg,'io'), cfg.io = struct(); end
if ~isfield(cfg.io,'transpose_if'), cfg.io.transpose_if = "auto"; end
if ~isfield(cfg.io,'outdir'), cfg.io.outdir = "results"; end
if ~isfield(cfg.io,'save_model'), cfg.io.save_model = true; end

% Resolve outdir relative to JSON folder (if not absolute)
baseDir = fileparts(jsonFile);
outdir = string(cfg.io.outdir);
if strlength(outdir)==0
    outdir = "results";
end
if ~isfolder(outdir) && ~isAbsolutePath(outdir)
    outdir = string(fullfile(baseDir, outdir));
end
cfg.io.outdir = outdir;
if ~isfolder(outdir), mkdir(outdir); end

% ----------------------------
% 1) Parse layout
% ----------------------------
layout = pme.parse_layout(cfg);

% ----------------------------
% 2) Load database
% ----------------------------
assert(isfield(cfg.io,'dbfile') && strlength(string(cfg.io.dbfile))>0, ...
    'cfg.io.dbfile is required in JSON (relative to case.json).');

dbfile = string(cfg.io.dbfile);
assert(isfile(dbfile), 'Database file not found: %s', dbfile);

% Your DB loader (keep it outside package if you prefer; here we call pme.load_db)
try
    [DB, meta] = pme.load_db(dbfile, struct('transpose_if', cfg.io.transpose_if));
catch
    [DB, meta] = pme.load_db(dbfile);
end

% ----------------------------
% 3) Ensure orientation (rows=Nfeatures, cols=Nsamples)
% ----------------------------
DB = enforce_db_orientation(DB, layout, cfg.io.transpose_if);

% ----------------------------
% 4) Filters (ONCE) + keep mask
% ----------------------------
DB_used = DB;
mask = true(1, size(DB,2));
filterInfo = struct();

if isfield(cfg,'filters') && ~isempty(cfg.filters)
    [DB_used, filterInfo, mask] = pme.filters(DB, cfg, layout);

    % Optional: explicit summary here (even if filters.m prints generic lines)
    fprintf('[run_case] filters cumulative kept %d / %d samples\n', sum(mask), size(DB,2));
else
    fprintf('[run_case] filters disabled: using all %d samples\n', size(DB,2));
end

% ----------------------------
% 5) Fit model on DB_used (NO filtering inside fit)
% ----------------------------
model = pme.fit(DB_used, cfg, layout);

% Attach mask + filterInfo for downstream consistency
model.filterMask = mask;
model.filterInfo = filterInfo;

% ----------------------------
% 6) Save model (optional)
% ----------------------------
saved = struct();
saved.model = false;
saved.model_file = "";

if cfg.io.save_model
    modelFile = fullfile(outdir, "model.mat");
    try
        pme.io("save", modelFile, model, cfg, layout, meta);
    catch
        save(modelFile, "model", "cfg", "layout", "meta", "-v7.3");
    end
    saved.model = true;
    saved.model_file = string(modelFile);
end

% ----------------------------
% 7) Report (optional)
% ----------------------------
rep = [];
doReport = logical(cfg.report.enable);

if doReport
    % report expects DB columns used during fit => DB_used
    rep = pme.report(model, DB_used, outdir);
else
    fprintf('[run_case] report disabled.\n');
end

% ----------------------------
% 8) Collect outputs
% ----------------------------
out = struct();
out.cfg     = cfg;
out.layout  = layout;
out.meta    = meta;
out.DB      = DB;         % original, oriented
out.DB_used = DB_used;    % filtered/used for fit
out.model   = model;
out.outdir  = outdir;
out.saved   = saved;
out.rep     = rep;

end

% ======================================================================

function DB = enforce_db_orientation(DB, layout, transpose_if)
% Ensure DB is [layout.totalRows x S] (features x samples).
% transpose_if: "never" | "always" | "auto"

tr = lower(string(transpose_if));
Nwant = layout.totalRows;

if tr == "always"
    DB = DB.';
    return;
elseif tr == "never"
    return;
end

% auto:
[nr,nc] = size(DB);
if nr == Nwant
    return;
end
if nc == Nwant
    DB = DB.';
    return;
end

error(['DB size does not match layout.totalRows.\n' ...
       '  layout.totalRows = %d\n' ...
       '  size(DB) = [%d x %d]\n' ...
       'Fix: check layout settings (geom/vars/phys) or transpose_if.'], ...
      Nwant, nr, nc);
end

function tf = isAbsolutePath(p)
p = string(p);
if strlength(p)==0, tf = false; return; end
if startsWith(p, "/"), tf = true; return; end
tf = ~isempty(regexp(char(p), '^[A-Za-z]:[\\/]', 'once'));
end
