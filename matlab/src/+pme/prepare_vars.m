function [Uact, Uinfo] = prepare_vars(Ubase, cfg, blocks, opts)
%PME.PREPARE_VARS Select active variables from Ubase and normalize to [0,1].
%
% Robust signature: supports calls with 2, 3, or 4 inputs:
%   [Uact,Uinfo] = pme.prepare_vars(Ubase, cfg)
%   [Uact,Uinfo] = pme.prepare_vars(Ubase, cfg, blocks)
%   [Uact,Uinfo] = pme.prepare_vars(Ubase, cfg, blocks, opts)
%
% opts.verbose (default true)
%
% NOTES (Option 1):
% - Urange can be provided as Mactx2 (only active variables).
% - If there are fixed variables (idx_fixed not empty) and Urange is Mactx2,
%   we DO NOT error: fixed variables are kept/handled in RAW space via fixed_policy.
% - In that case, Uinfo.Urange_fixed_available = false.

% ---- defaults for optional args ----
if nargin < 3 || isempty(blocks), blocks = struct(); end %#ok<NASGU>
if nargin < 4 || isempty(opts), opts = struct(); end
if ~isfield(opts,'verbose') || isempty(opts.verbose), opts.verbose = true; end

Uinfo = struct();

% ---- basic sizes ----
assert(isfield(cfg,'vars') && isfield(cfg.vars,'Mbase'), 'cfg.vars.Mbase is required.');
Mbase = cfg.vars.Mbase;
S = size(Ubase,2);
assert(size(Ubase,1) == Mbase, 'Ubase rows must equal cfg.vars.Mbase');

% ---- idx_active default ----
idx_active = [];
if isfield(cfg.vars,'idx_active')
    idx_active = cfg.vars.idx_active;
end
if isempty(idx_active)
    idx_active = 1:Mbase;
end
idx_active = unique(idx_active(:)','stable');
assert(all(idx_active>=1 & idx_active<=Mbase), 'idx_active out of range');
Mact = numel(idx_active);

idx_all   = 1:Mbase;
idx_fixed = setdiff(idx_all, idx_active, 'stable');

Uinfo.idx_active = idx_active;
Uinfo.idx_fixed  = idx_fixed;
Uinfo.Mact       = Mact;
Uinfo.Mbase      = Mbase;

% ---- fixed policy ----
fixed_policy = "baseline";
if isfield(cfg.vars,'fixed_policy') && ~isempty(cfg.vars.fixed_policy)
    fixed_policy = string(cfg.vars.fixed_policy);
end
Uinfo.fixed_policy = fixed_policy;

% baseline_col robust
if ~isfield(cfg,'baseline_col') || isempty(cfg.baseline_col)
    cfg.baseline_col = 1;
end

% baseline/fixed RAW values
switch lower(fixed_policy)

    case "baseline"
        bcol = max(1, min(cfg.baseline_col, S));
        Ubase_baseline_raw = Ubase(:, bcol);
        if ~isempty(idx_fixed), Ubase_fixed_raw = Ubase_baseline_raw(idx_fixed);
        else, Ubase_fixed_raw = [];
        end

    case "from_dbcol"
        assert(isfield(cfg.vars,'fixed_col') && ~isempty(cfg.vars.fixed_col), ...
            'fixed_policy="from_dbcol" requires cfg.vars.fixed_col');
        fcol = max(1, min(cfg.vars.fixed_col, S));
        Ubase_baseline_raw = Ubase(:, fcol);
        if ~isempty(idx_fixed), Ubase_fixed_raw = Ubase_baseline_raw(idx_fixed);
        else, Ubase_fixed_raw = [];
        end

    case "from_ref"
        assert(isfield(cfg.vars,'Uref') && ~isempty(cfg.vars.Uref), ...
            'fixed_policy="from_ref" requires cfg.vars.Uref');
        Uref = cfg.vars.Uref;
        assert(isnumeric(Uref) && numel(Uref)==Mbase, 'Uref must be Mbase x 1');
        Ubase_baseline_raw = Uref(:);
        if ~isempty(idx_fixed), Ubase_fixed_raw = Ubase_baseline_raw(idx_fixed);
        else, Ubase_fixed_raw = [];
        end

    otherwise
        error('Unknown fixed_policy: %s', fixed_policy);
end

Uinfo.Ubase_baseline_raw = Ubase_baseline_raw;
Uinfo.Ubase_fixed_raw    = Ubase_fixed_raw;

% ---- Urange (robust) ----
Ur = [];
if isfield(cfg.vars,'Urange')
    Ur = cfg.vars.Urange;
end

% If Urange is struct (from load(.mat)), try to extract numeric matrix
if isstruct(Ur)
    fn = fieldnames(Ur);
    found = [];
    for i=1:numel(fn)
        v = Ur.(fn{i});
        if isnumeric(v) && ismatrix(v) && size(v,2)==2
            found = v; break;
        end
    end
    Ur = found;
end

if isempty(Ur)
    if isfield(cfg.vars,'use_db_range_if_missing') && cfg.vars.use_db_range_if_missing
        Ur_full = [min(Ubase,[],2) max(Ubase,[],2)];  % [Mbase x 2]
        Uinfo.Urange_source = "db";
    else
        Ur_full = [];
        Uinfo.Urange_source = "missing";
    end
else
    Uinfo.Urange_source = "user";
    Ur_full = Ur;
end

if ~isempty(Ur_full)
    assert(isnumeric(Ur_full) && size(Ur_full,2)==2, ...
        'Urange must be numeric with 2 columns [min max].');

    if size(Ur_full,1) == Mbase
        % ok
    elseif size(Ur_full,1) == Mact
        % expand to Mbase with NaNs for fixed vars (Option 1 allowed)
        tmp = nan(Mbase,2);
        tmp(idx_active,:) = Ur_full;
        Ur_full = tmp;
    else
        error('Urange must be Mbase x 2 or Mact x 2. Got %d x %d.', size(Ur_full,1), size(Ur_full,2));
    end

    Ur_act = Ur_full(idx_active,:);
else
    Ur_act = [];
end

Uinfo.Urange = Ur_act;

% ---- normalize active ----
Uraw_act = Ubase(idx_active,:);

if isempty(Ur_act)
    warning('[vars] Urange missing: returning raw Uact (NOT normalized).');
    Uact = Uraw_act;

    Uinfo.min_before_clip = min(Uact(:));
    Uinfo.max_before_clip = max(Uact(:));
    Uinfo.min_after_clip  = Uinfo.min_before_clip;
    Uinfo.max_after_clip  = Uinfo.max_before_clip;

    % baseline/fixed "norm" fall back to raw
    Uinfo.Ubase_baseline_norm = Ubase_baseline_raw;
    Uinfo.Ubase_fixed_norm    = Ubase_fixed_raw;
    Uinfo.Urange_fixed_available = false;
    return;
end

Umin = Ur_act(:,1);
Umax = Ur_act(:,2);
den  = max(Umax - Umin, eps);
Uact = (Uraw_act - Umin) ./ den;

% baseline normalized (active components only; useful if inverse uses normalized space)
Ubase_baseline_norm = (Ubase_baseline_raw(idx_active) - Umin) ./ den;
Uinfo.Ubase_baseline_norm = Ubase_baseline_norm;

% ---- fixed vars: Option 1 behaviour ----
% If Urange was provided only for actives => Ur_full has NaNs on fixed rows.
% In that case, we do NOT normalize fixed vars; they stay in RAW and are handled by fixed_policy.
if ~isempty(idx_fixed)
    Ur_fix = Ur_full(idx_fixed,:);
    if any(isnan(Ur_fix(:)))
        % Urange for fixed vars not available (this is allowed)
        Uinfo.Ubase_fixed_norm = [];
        Uinfo.Urange_fixed_available = false;

        if opts.verbose
            fprintf('[vars] Urange provided only for active vars (Mactx2). Fixed vars kept in RAW via fixed_policy=%s.\n', ...
                lower(string(fixed_policy)));
        end
    else
        UminF = Ur_fix(:,1);
        UmaxF = Ur_fix(:,2);
        denF  = max(UmaxF - UminF, eps);
        Ubase_fixed_norm = (Ubase_fixed_raw - UminF) ./ denF;

        Uinfo.Ubase_fixed_norm = Ubase_fixed_norm;
        Uinfo.Urange_fixed_available = true;
    end
else
    Uinfo.Ubase_fixed_norm = [];
    Uinfo.Urange_fixed_available = true;
end

% diagnostics + clip
Uinfo.min_before_clip = min(Uact(:));
Uinfo.max_before_clip = max(Uact(:));

tol = 1e-6;
if Uinfo.min_before_clip < -tol || Uinfo.max_before_clip > 1+tol
    warning('[vars] Uact out of [0,1] before clip: min=%.4g max=%.4g. Clipping to [0,1].', ...
        Uinfo.min_before_clip, Uinfo.max_before_clip);
end

Uact = min(max(Uact,0),1);

Uinfo.min_after_clip = min(Uact(:));
Uinfo.max_after_clip = max(Uact(:));

if opts.verbose
    fprintf('[vars] normalized Uact using %s Urange; min/max after clip = %.4g / %.4g (Mact=%d)\n', ...
        Uinfo.Urange_source, Uinfo.min_after_clip, Uinfo.max_after_clip, Mact);
end

end
