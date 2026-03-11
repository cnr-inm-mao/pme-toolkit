function out = backmapping(cfg_json, varargin)
%PME.BACKMAPPING Standalone backmapping from reduced variables to original variables.
%
% Reconstructs original variables directly from the saved reduced model:
%   P_hat = P0 + delta_m + Zr * alpha
%
% Then:
%   1) extracts the active-variable block from P_hat
%   2) denormalizes active variables using model.Uinfo.Urange
%   3) reinserts active variables into full-space Ubase using
%      model.Uinfo.Ubase_baseline_raw
%
% This function is intentionally standalone and does NOT call pme.inverse.
%
% Usage:
%   pme.backmapping("backmapping.json")
%   pme.backmapping("backmapping.json","x01",[...])
%
% Minimal JSON schema:
% {
%   "case_json": "PATH/TO/case.json",
%   "input":  { "file":"results/x01.txt", "format":"txt" },
%   "reduced_space": { "nconf": 5 },
%   "denorm": { "rule":"3sigma", "c":3.0 },
%   "output": {
%       "file":"results/u_base.txt",
%       "format":"txt",
%       "layout":"col",
%       "what":"Ubase",
%       "write_meta":true
%   }
% }
%
% Notes:
% - Paths in input/output are resolved relative to the folder containing case.json,
%   unless they are absolute.
% - Default I/O: txt (one number per line), output layout "col".
% - Input x01 is assumed in [0,1]^k.
% - Denorm rules:
%     minmax: alpha in [min(alpha_train), max(alpha_train)] using model.alfak
%     3sigma: alpha in [-c*sqrt(lambda), +c*sqrt(lambda)] using model.Lr
%
% Output struct fields:
%   out.case_dir
%   out.outdir
%   out.model_file
%   out.x01
%   out.alpha
%   out.P
%   out.Uact
%   out.U
%   out.written_files

% -------------------- parse varargin --------------------
p = inputParser;
p.addRequired('cfg_json', @(s)ischar(s)||isstring(s));
p.addParameter('x01', [], @(x)isnumeric(x));
p.addParameter('dry_run', false, @(x)islogical(x)&&isscalar(x));
p.parse(cfg_json, varargin{:});

x01_override = p.Results.x01;
dry_run = p.Results.dry_run;

cfg_json = string(cfg_json);
assert(isfile(cfg_json), 'Config JSON not found: %s', cfg_json);

cfgBM = jsondecode(fileread(cfg_json));
assert(isfield(cfgBM,'case_json') && strlength(string(cfgBM.case_json))>0, ...
    'backmapping.json must contain "case_json".');

% -------------------- resolve case paths --------------------
case_json = string(cfgBM.case_json);
cfgDir = string(fileparts(cfg_json));
case_json = resolve_path(case_json, cfgDir);
assert(isfile(case_json), 'case_json not found: %s', case_json);

case_dir = string(fileparts(case_json));

% canonical case config -> exact outdir like run_case
caseCfg = pme.read_case_json(case_json);

if ~isfield(caseCfg,'io'), caseCfg.io = struct(); end
if ~isfield(caseCfg.io,'outdir') || strlength(string(caseCfg.io.outdir))==0
    caseCfg.io.outdir = "results";
end

outdir = string(caseCfg.io.outdir);
if ~isfolder(outdir) && ~isAbsolutePath(outdir)
    outdir = string(fullfile(case_dir, outdir));
end

% -------------------- model file --------------------
model_file = fullfile(outdir, "model.mat");
if isfield(cfgBM,'run_case') && isfield(cfgBM.run_case,'model_file') && ~isempty(cfgBM.run_case.model_file)
    model_file = resolve_path(string(cfgBM.run_case.model_file), case_dir);
end
assert(isfile(model_file), 'Model file not found: %s', model_file);

model_var = "model";
if isfield(cfgBM,'run_case') && isfield(cfgBM.run_case,'model_var') && ~isempty(cfgBM.run_case.model_var)
    model_var = string(cfgBM.run_case.model_var);
end

S = load(model_file);
assert(isfield(S, model_var), 'Variable "%s" not found in %s', model_var, model_file);
model = S.(model_var);

% -------------------- read x01 --------------------
if ~isempty(x01_override)
    x01 = x01_override(:);
else
    assert(isfield(cfgBM,'input'), ...
        'backmapping.json must contain "input" (or provide x01 override).');
    assert(isfield(cfgBM.input,'file') && ~isempty(cfgBM.input.file), ...
        'input.file is required if no x01 override.');

    in_file = resolve_path(string(cfgBM.input.file), case_dir);

    in_fmt = "txt";
    if isfield(cfgBM.input,'format') && ~isempty(cfgBM.input.format)
        in_fmt = lower(string(cfgBM.input.format));
    end

    x01 = read_vector(in_file, in_fmt);
end

% -------------------- choose number of reduced vars --------------------
k_model = infer_k(model);
nconf_use = k_model;

if isfield(cfgBM,'reduced_space') && isfield(cfgBM.reduced_space,'nconf') && ~isempty(cfgBM.reduced_space.nconf)
    nconf_use = double(cfgBM.reduced_space.nconf);
end

assert(nconf_use >= 1 && nconf_use <= k_model, ...
    'reduced_space.nconf must be between 1 and %d (got %d).', k_model, nconf_use);

x01 = x01(:);
assert(numel(x01)==nconf_use, ...
    'x01 length must be nconf_use=%d (got %d).', nconf_use, numel(x01));
assert(all(isfinite(x01)), 'x01 contains NaN/Inf.');
assert(all(x01>=0 & x01<=1), 'x01 must be in [0,1].');

% -------------------- truncated model view --------------------
model_use = model;
model_use.Zr = model.Zr(:,1:nconf_use);

if isfield(model,'Lr') && ~isempty(model.Lr)
    model_use.Lr = model.Lr(1:nconf_use);
end

if isfield(model,'alfak') && ~isempty(model.alfak)
    model_use.alfak = model.alfak(1:nconf_use,:);
end

if isfield(model_use,'cfg')
    model_use.cfg.nconf = nconf_use;
end

% -------------------- denormalize x01 -> alpha --------------------
rule = "3sigma";
c = 3.0;
if isfield(cfgBM,'denorm') && isfield(cfgBM.denorm,'rule') && ~isempty(cfgBM.denorm.rule)
    rule = lower(string(cfgBM.denorm.rule));
end
if isfield(cfgBM,'denorm') && isfield(cfgBM.denorm,'c') && ~isempty(cfgBM.denorm.c)
    c = double(cfgBM.denorm.c);
end

[amin, amax, rule_used] = alpha_bounds_from_model(model_use, rule, c);

amin = amin(:);
amax = amax(:);

assert(numel(amin)==nconf_use, 'amin has length %d, expected %d.', numel(amin), nconf_use);
assert(numel(amax)==nconf_use, 'amax has length %d, expected %d.', numel(amax), nconf_use);

% alpha is kept as column for standalone reconstruction
alpha_col = amin + x01 .* (amax - amin);   % [k x 1]
alpha_row = alpha_col.';                   % [1 x k], only for reporting if needed

% -------------------- standalone reconstruction --------------------
if dry_run
    P_hat = [];
    Uact_raw = [];
    Ubase = [];
else
    % 1) reduced reconstruction in embedded space
    % model_use.Zr: [Np x k], alpha_col: [k x 1]
    Pc_hat = model_use.Zr * alpha_col;                     % [Np x 1]

    assert(isfield(model_use,'delta_m') && ~isempty(model_use.delta_m), ...
        'Missing model.delta_m in model.mat.');
    assert(isfield(model_use,'P0') && ~isempty(model_use.P0), ...
        'Missing model.P0 in model.mat.');

    P_hat = Pc_hat + model_use.delta_m + model_use.P0;    % [Np x 1]

    % 2) extract active-variable block from P_hat
    if isfield(model_use,'Uinfo') && isfield(model_use.Uinfo,'idx_active') && ~isempty(model_use.Uinfo.idx_active)
        idxA = model_use.Uinfo.idx_active(:);
    elseif isfield(model_use,'cfg') && isfield(model_use.cfg,'vars') && ...
           isfield(model_use.cfg.vars,'idx_active') && ~isempty(model_use.cfg.vars.idx_active)
        idxA = model_use.cfg.vars.idx_active(:);
    else
        error('Missing active-variable indices: neither model.Uinfo.idx_active nor model.cfg.vars.idx_active is available.');
    end
    
    Mact = numel(idxA);

    assert(isfield(model_use,'layout'), 'Missing model.layout.');
    assert(isfield(model_use,'cfg') && isfield(model_use.cfg,'mode'), 'Missing model.cfg.mode.');

    mode = lower(string(model_use.cfg.mode));

    switch mode
        case {"pme","pi"}
            assert(isfield(model_use.layout,'D') && isfield(model_use.layout.D,'nRows'), ...
                'For mode=%s, expected model.layout.D.nRows.', mode);
            i0 = model_use.layout.D.nRows + 1;

        case "pd"
            i0 = 1;

        otherwise
            error('Unknown mode: %s', mode);
    end

    i1 = i0 + Mact - 1;
    assert(i1 <= numel(P_hat), ...
        'Active-variable block exceeds P size: i1=%d, numel(P_hat)=%d.', i1, numel(P_hat));

    Uact_hat = P_hat(i0:i1);    % normalized active variables in P-space

    % 3) denormalize active variables to original/raw variables
    assert(isfield(model_use,'Uinfo') && isfield(model_use.Uinfo,'Urange') && ~isempty(model_use.Uinfo.Urange), ...
        'Missing model.Uinfo.Urange for active-variable denormalization.');

    Ur = model_use.Uinfo.Urange;
    assert(size(Ur,1) >= Mact && size(Ur,2) >= 2, ...
        'model.Uinfo.Urange must be at least [Mact x 2].');

    Umin = Ur(1:Mact,1);
    Umax = Ur(1:Mact,2);
    dU   = Umax - Umin;
    dU(abs(dU) < eps) = 1.0;  % avoid division issues / degenerate ranges

    Uact_raw = Uact_hat(:) .* dU + Umin;

    % 4) rebuild full-space Ubase using stored raw baseline
    if isfield(model_use,'cfg') && isfield(model_use.cfg,'vars') && ...
       isfield(model_use.cfg.vars,'Mbase') && ~isempty(model_use.cfg.vars.Mbase)
        Mbase = model_use.cfg.vars.Mbase;
    elseif isfield(model_use,'Uinfo') && isfield(model_use.Uinfo,'Mbase') && ~isempty(model_use.Uinfo.Mbase)
        Mbase = model_use.Uinfo.Mbase;
    else
        error('Missing Mbase: neither model.cfg.vars.Mbase nor model.Uinfo.Mbase is available.');
    end

    assert(isfield(model_use,'Uinfo') && isfield(model_use.Uinfo,'Ubase_baseline_raw') && ...
           ~isempty(model_use.Uinfo.Ubase_baseline_raw), ...
           'Missing model.Uinfo.Ubase_baseline_raw.');

    Ubase = model_use.Uinfo.Ubase_baseline_raw(:);
    assert(numel(Ubase) == Mbase, ...
        'Ubase_baseline_raw length mismatch: expected %d, got %d.', Mbase, numel(Ubase));

    Ubase(idxA) = Uact_raw;
end

% -------------------- choose output --------------------
what = "Ubase";
if isfield(cfgBM,'output') && isfield(cfgBM.output,'what') && ~isempty(cfgBM.output.what)
    what = string(cfgBM.output.what);
end

switch lower(what)
    case "ubase"
        U = Ubase;
    case "uact"
        U = Uact_raw;
    case "p"
        U = P_hat;
    case "alpha"
        U = alpha_col;
    otherwise
        error('Unsupported output.what="%s". Use Ubase, Uact, P, or alpha.', what);
end

U = U(:);

% -------------------- output settings --------------------
assert(isfield(cfgBM,'output') && isfield(cfgBM.output,'file') && ~isempty(cfgBM.output.file), ...
    'output.file is required.');

out_file = resolve_path(string(cfgBM.output.file), case_dir);

out_fmt = "txt";
if isfield(cfgBM.output,'format') && ~isempty(cfgBM.output.format)
    out_fmt = lower(string(cfgBM.output.format));
end

layout = "col";
if isfield(cfgBM.output,'layout') && ~isempty(cfgBM.output.layout)
    layout = lower(string(cfgBM.output.layout));
end

write_meta = true;
if isfield(cfgBM.output,'write_meta') && ~isempty(cfgBM.output.write_meta)
    write_meta = logical(cfgBM.output.write_meta);
end

% -------------------- write outputs --------------------
written = struct('vector_file',"",'meta_file',"");

if ~dry_run
    tmp = out_file + ".tmp";
    write_vector(tmp, out_fmt, U, layout);
    movefile(tmp, out_file, 'f');
    written.vector_file = out_file;

    if write_meta
        meta = struct();
        meta.schema = "pme.backmapping.v1";
        meta.case_json = char(case_json);
        meta.model_file = char(model_file);
        meta.what = char(what);
        meta.nconf_model = k_model;
        meta.nconf_use = nconf_use;
        meta.m = numel(U);
        meta.denorm = struct('rule', char(rule_used), 'c', c);
        meta.x01_file = "";
        if isempty(x01_override)
            meta.x01_file = char(resolve_path(string(cfgBM.input.file), case_dir));
        else
            meta.x01_file = "(override)";
        end
        meta.created_at = char(datetime('now','TimeZone','Europe/Rome', ...
            'Format',"yyyy-MM-dd'T'HH:mm:ssXXX"));

        meta_file = out_file + ".meta.json";
        fid = fopen(meta_file,'w');
        assert(fid>0, 'Cannot write %s', meta_file);
        fwrite(fid, jsonencode(meta), 'char');
        fclose(fid);
        written.meta_file = meta_file;
    end
end

% -------------------- return struct --------------------
out = struct();
out.case_dir = char(case_dir);
out.outdir = char(outdir);
out.model_file = char(model_file);
out.x01 = x01(:);
out.alpha = alpha_col(:);
out.P = P_hat;
out.Uact = Uact_raw;
out.U = U;
out.written_files = written;

if ~dry_run
    fprintf('[pme.backmap] wrote %s (%s)\n', out_file, out_fmt);
end

end

% ======================================================================
% Local helpers
% ======================================================================

function v = read_vector(file, format)
format = lower(string(format));
assert(isfile(file), "Input file not found: %s", file);

switch format
    case "txt"
        v = readmatrix(file, "FileType","text");
        v = v(:);

    case "csv"
        A = readmatrix(file);
        assert(~isempty(A), "Empty csv: %s", file);

        if size(A,1)==1 && size(A,2)>=1
            v = A(:);
        elseif size(A,2)==1 && size(A,1)>=1
            v = A(:);
        else
            error("CSV must be a single row or single column (got %dx%d): %s", ...
                size(A,1), size(A,2), file);
        end

    otherwise
        error("Unknown vector format: %s (use txt|csv)", format);
end

assert(all(isfinite(v)), "Vector contains NaN/Inf: %s", file);
end

function write_vector(file, format, v, layout)
format = lower(string(format));
layout = lower(string(layout));
v = v(:);

ensure_parent_dir(file);

switch format
    case "txt"
        fid = fopen(file,'w');
        assert(fid>0, 'Cannot write %s', file);
        fprintf(fid, '%.17g\n', v);
        fclose(fid);

    case "csv"
        switch layout
            case "row"
                writematrix(v.', file);
            case "col"
                writematrix(v, file);
            otherwise
                error('output.layout must be "row" or "col" for csv.');
        end

    otherwise
        error("Unknown output format: %s (use txt|csv)", format);
end
end

function k = infer_k(model)
if isfield(model,'cfg') && isfield(model.cfg,'nconf') && ~isempty(model.cfg.nconf)
    k = double(model.cfg.nconf);
    return;
end

if isfield(model,'Zr') && ~isempty(model.Zr)
    k = size(model.Zr,2);
    return;
end

error('Cannot infer k (nconf/Zr missing from model).');
end

function [amin,amax,rule_used] = alpha_bounds_from_model(model, rule, c)
k = infer_k(model);
rule = lower(string(rule));

switch rule
    case "minmax"
        assert(isfield(model,'alfak') && ~isempty(model.alfak), ...
            'minmax requires model.alfak (k x 2).');
        B = model.alfak;
        assert(size(B,1)>=k && size(B,2)>=2, 'model.alfak must be at least kx2.');
        amin = B(1:k,1);
        amax = B(1:k,2);
        rule_used = "minmax";

    case "3sigma"
        assert(isfield(model,'Lr') && ~isempty(model.Lr), ...
            '3sigma requires model.Lr (k x 1).');
        Lr = model.Lr(:);
        assert(numel(Lr)>=k, 'model.Lr must have at least k elements.');
        sig = sqrt(Lr(1:k));
        amin = -c * sig;
        amax = +c * sig;
        rule_used = "3sigma";

    otherwise
        error('Unknown denorm.rule: %s (use minmax|3sigma)', rule);
end
end

function p = resolve_path(p, baseDir)
p = string(p);
if strlength(p)==0
    return;
end
if isAbsolutePath(p)
    return;
end
p = string(fullfile(baseDir, p));
end

function tf = isAbsolutePath(p)
p = string(p);
if strlength(p)==0
    tf = false;
    return;
end
if startsWith(p, "/")
    tf = true;
    return;
end
tf = ~isempty(regexp(char(p), '^[A-Za-z]:[\\/]', 'once'));
end

function ensure_parent_dir(filepath)
filepath = string(filepath);
[parent,~,~] = fileparts(filepath);
if strlength(string(parent))>0 && ~isfolder(parent)
    mkdir(parent);
end
end