function model = fit(DB, cfg, layout, opts)
%PME.FIT Fit PME / PI-PME / PD-PME on a database matrix DB (Nfeatures x Nsamp).
%
%   model = pme.fit(DB, cfg)
%   model = pme.fit(DB, cfg, layout)
%   model = pme.fit(DB, cfg, layout, opts)
%
% DB is expected to be already oriented as [Nfeatures x Nsamp].
% By default, this function DOES NOT apply filters. Filtering should be done
% once in pme.run_case() to keep bookkeeping consistent.
%
% opts (optional):
%   opts.apply_filters (logical) : if true, apply pme.filters inside fit (default: false)
%
% Output model contains eig info, weights, and diagnostics.
% If filters are applied inside, model.filterMask and model.filterInfo are filled.

arguments
    DB double
    cfg struct
    layout struct = struct()
    opts.apply_filters (1,1) logical = false
end

% ---- defaults + layout ----
cfg = pme.defaults(cfg);

if nargin < 3 || isempty(fieldnames(layout))
    layout = pme.parse_layout(cfg);
end

if size(DB,1) < layout.totalRows
    error('DB has %d rows but layout expects at least %d.', size(DB,1), layout.totalRows);
end

% ---- optionally filter (DISCOURAGED in new pipeline; prefer run_case) ----
DB_used = DB;
mask = true(1, size(DB,2));
filterInfo = struct();

if opts.apply_filters && isfield(cfg,'filters')
    [DB_used, filterInfo, mask] = pme.filters(DB, cfg, layout);
end

% ---- build P-space ----
blocks = pme.slice(DB_used, layout);

% Prepare vars (should normalize if Urange is provided; you will fix prepare_vars)
[Uact, Uinfo] = pme.prepare_vars(blocks.Ubase, cfg, blocks, struct('verbose', true));

P = pme.compose_P(blocks.D, Uact, blocks.F, blocks.C, cfg);

S  = size(P,2);

% Baseline column (already converted to 1-based in read_case_json)
if ~isfield(cfg,'baseline_col') || isempty(cfg.baseline_col)
    cfg.baseline_col = 1;
end
if cfg.baseline_col < 1 || cfg.baseline_col > S
    error('baseline_col=%d is out of bounds for P with S=%d columns.', cfg.baseline_col, S);
end

P0 = P(:, cfg.baseline_col);

delta   = P - P0;
delta_m = mean(delta, 2);
Pc      = delta - delta_m;

% ---- weights ----
[W, statsW] = pme.weights(delta, layout, cfg, Uinfo, blocks);

% ---- covariance + eig ----
A  = (Pc*Pc')/S;
AW = A*W;

[Z, Laux] = eig(AW);
Lraw = real(diag(Laux));

% Sort descending
[L, I] = sort(Lraw, 'descend');
Zs = Z(:, I);

% Normalize eigenvectors in W-inner-product: Z' W Z = I
an = diag(Zs' * W * Zs);
an = sqrt(max(an, eps));
Zn = Zs ./ (an');  % normalize columns

% Choose nconf
nconf = pme.choose_nconf(L, cfg.CI);

% Reduced basis
Zr = Zn(:,1:nconf);
Lr = L(1:nconf);

% Coordinates (full and reduced)
ak_full = Pc' * W * Zn;     % [S x N]
alpha   = ak_full(:,1:nconf);

% alpha statistics (your alfak)
alfak = zeros(nconf,3);
for j=1:nconf
    alfak(j,1) = min(alpha(:,j));
    alfak(j,2) = max(alpha(:,j));
    alfak(j,3) = mean(alpha(:,j).^2);
end

% ---- pack model ----
model = struct();
model.version = "1.2";
model.mode    = string(cfg.mode);
model.cfg     = cfg;
model.layout  = layout;

% Filtering bookkeeping (empty unless opts.apply_filters=true or set by run_case)
model.filterInfo = filterInfo;
model.filterMask = mask;

model.P0      = P0;
model.delta_m = delta_m;
model.W       = W;

model.Zr     = Zr;
model.Lr     = Lr;
model.alfak  = alfak;

% Diagnostics
model.L_full  = L;
model.Z_full  = Zn;
model.ak_full = ak_full;
model.statsW  = statsW;
model.Uinfo   = Uinfo;

model.sizes = struct();
model.sizes.DB_rows      = size(DB,1);
model.sizes.DB_cols      = size(DB,2);
model.sizes.DB_used_cols = size(DB_used,2);
model.sizes.P_rows       = size(P,1);
model.sizes.P_cols       = size(P,2);
model.sizes.nconf        = nconf;

end
