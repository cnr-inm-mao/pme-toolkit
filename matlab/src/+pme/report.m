function rep = report(model, DB_used, outdir)
%PME.REPORT Sanity checks + plots + NMSE/VARP per information source.
%
% Key conventions:
% - Variables U are NEVER treated as information sources.
% - Sources ordering: FIELDS first, then SCALARS (physics order).
% - PME/PI: include GEOM (D) as first source. PD: no geom source.
% - NMSE is computed for k = 1..nconf (NOT including k=0).
%
% Saves:
% - report.mat (rep struct)
% - pme_varp.mat (var_p) if ninf>0
% - variance_retained.png
% - scree_plot.png
% - nmse_by_source.png      (if ninf>0)
% - variance_by_source.png  (if ninf>0)
% - mode_01.png, mode_02.png, mode_03.png (if geometry exists)

if nargin < 3 || isempty(outdir)
    outdir = fullfile(pwd,'results');
end
if ~isfolder(outdir), mkdir(outdir); end

cfg    = model.cfg;
layout = model.layout;
mode   = lower(string(cfg.mode));

% --- active vars count (robust) ---
if isfield(model,'Uinfo') && isfield(model.Uinfo,'idx_active') && ~isempty(model.Uinfo.idx_active)
    Mact = numel(model.Uinfo.idx_active);
else
    Mact = cfg.vars.Mbase;
end

% --- rebuild P and Pc consistently from DB_used ---
blocks = pme.slice(DB_used, layout);
[Uact, ~] = pme.prepare_vars(blocks.Ubase, cfg, blocks, struct('verbose', false));
Ptrue = pme.compose_P(blocks.D, Uact, blocks.F, blocks.C, cfg);

S = size(Ptrue,2);
nconf = model.sizes.nconf;

delta = Ptrue - model.P0;
Pc    = delta - model.delta_m;   % [Np x S] centered signal

% --- row positions of blocks in P ---
pos = pme_report_p_blocks(model, size(Ptrue,1), Mact);

% --- compute ninf according to your definition ---
[ninf, nphys] = pme_compute_ninf_from_layout(model);

% --- pack rep ---
rep = struct();
rep.mode  = string(mode);
rep.CI    = cfg.CI;
rep.S     = S;
rep.Mact  = Mact;
rep.nconf = nconf;
rep.ninf  = ninf;
rep.nphys = nphys;
rep.pos   = pos;

% =========================
% 1) Variance sanity check
% =========================
rep.var = struct();
rep.var.total = sum(var(Pc, 1, 2));
rep.var.geom  = block_var(Pc, pos.D);
rep.var.vars  = block_var(Pc, pos.U);

rep.var.fields  = [];
rep.var.scalars = [];

if ~isempty(pos.F) && isfield(layout,'F') && layout.F.nRows > 0
    rep.var.fields = compute_field_vars(Pc, pos.F, layout);
end
if ~isempty(pos.C) && isfield(layout,'C') && layout.C.nRows > 0
    rep.var.scalars = compute_scalar_vars(Pc, pos.C, layout);
end

fprintf('\n[pme.report] ===== SANITY CHECK: variance by component =====\n');
fprintf('[pme.report] mode=%s, S=%d, Mact=%d, CI=%.4f\n', rep.mode, S, Mact, cfg.CI);
fprintf('[pme.report] var_geom    d  = %.6e (rows=%d)\n', rep.var.geom, numel(pos.D));
fprintf('[pme.report] var_vars    u  = %.6e (rows=%d)\n', rep.var.vars, numel(pos.U));

if ~isempty(rep.var.fields)
    for i=1:numel(rep.var.fields)
        fprintf('[pme.report] var_field   %-2s = %.6e (rows=%d)\n', ...
            rep.var.fields(i).name, rep.var.fields(i).var, rep.var.fields(i).nRows);
    end
end
if ~isempty(rep.var.scalars)
    for i=1:numel(rep.var.scalars)
        fprintf('[pme.report] var_scalar  %-2s = %.6e (rows=%d)\n', ...
            rep.var.scalars(i).name, rep.var.scalars(i).var, rep.var.scalars(i).nRows);
    end
end

% ==========================================
% 2) Dimensionality reduction summary print
% ==========================================
reduction_pct = 100*(1 - nconf/max(Mact,1));
fprintf('\n[pme.report] ===== DIMENSIONALITY REDUCTION RESULT =====\n');
fprintf('[pme.report] N modes needed for CI=%.4f: %d\n', cfg.CI, nconf);
fprintf('[pme.report] reduced from Mact=%d to N=%d  ->  %.2f %% reduction\n', ...
    Mact, nconf, reduction_pct);
fprintf('[pme.report] number of information sources = %d\n', ninf);

% ==========================================
% 3) NMSE per information source
% ==========================================
rep.nmse = struct();
rep.nmse.enable = (ninf > 0);

kplot = min(Mact, size(model.Z_full,2));   % full curve length
krep  = min(nconf, kplot);                 % reported value at k=nconf

rep.nmse.k_grid = 1:kplot;
rep.kmax = kplot;
rep.krep = krep;

if rep.nmse.enable
    sources = pme_build_info_sources(pos, layout, mode);

    assert(numel(sources) == ninf, ...
        'Internal mismatch: sources(%d) != ninf(%d).', numel(sources), ninf);

    % Variance per source (denominator): sum of per-row variances
    var_src = zeros(ninf,1);
    for i = 1:ninf
        rr = sources(i).rows;
        var_src(i) = sum(var(Pc(rr,:), 1, 2));
    end

    nmse_t = zeros(ninf, kplot);   % columns correspond to k = 1..kplot

    for jconf = 1:kplot
        k = jconf; % k modes
        Prec = model.Z_full(:,1:k) * (model.ak_full(:,1:k)');  % [Np x S]
        E = Pc - Prec;

        for i = 1:ninf
            rr = sources(i).rows;
            mse_block = mean(sum(E(rr,:).^2, 1)); % mean over samples
            nmse_t(i, jconf) = mse_block / max(var_src(i), eps);
        end
    end

    var_t = 1 - nmse_t;
    nmse_t = real(nmse_t);
    var_t  = real(var_t);

    % incremental contribution per added mode
    var_p = zeros(ninf, kplot);
    var_p(:,1) = var_t(:,1);
    for j = 2:kplot
        var_p(:,j) = var_t(:,j) - var_t(:,j-1);
    end

    rep.nmse.sources = sources;
    rep.nmse.var_src = var_src;
    rep.nmse.nmse_t  = nmse_t;
    rep.nmse.var_t   = var_t;
    rep.nmse.var_p   = var_p;

    fprintf('\n[pme.report] ===== NMSE (per information source) =====\n');
    fprintf('[pme.report] k-grid = 1..kplot (printed: k=nconf)\n');
    for i = 1:ninf
        fprintf('[pme.report] NMSE %-5s = %.6g\n', string(sources(i).name), nmse_t(i,krep));
    end
    
    % ---- Global check (consistent with W: each info has weight 1) ----
    nmse_global = mean(nmse_t, 1);   % 1 x kplot
    ev_global   = 1 - nmse_global;   % 1 x kplot
    
    lam = model.L_full(:);
    lam_cum = cumsum(lam(1:kplot)).' / max(double(ninf), eps);  % 1 x kplot

    rep.nmse.nmse_global  = nmse_global;
    rep.nmse.ev_global    = ev_global;
    rep.nmse.lam_cum_ninf = lam_cum;

    fprintf('[pme.report] NMSE %-5s = %.6g\n', 'total', nmse_global(krep));


    fprintf('\n[pme.report] ===== GLOBAL CHECK (W-consistent) =====\n');
    fprintf('[pme.report] 1 - NMSE_total at k=nconf = %.6g\n', ev_global(krep));
    fprintf('[pme.report] sum(lambda_1..k)/ninf at k=nconf = %.6g\n', lam_cum(krep));
    fprintf('[pme.report] diff = %.3g\n', ev_global(krep) - lam_cum(krep));

    try
        save(fullfile(outdir,'pme_varp.mat'),'var_p','-v7');
    catch
        save(fullfile(outdir,'pme_varp.mat'),'var_p','-v7.3');
    end
end

% =========================
% 4) Plots
% =========================
L = model.L_full(:);

try
    pme.plot_variance_retained(model, outdir);
catch ME
    warning('[pme.report] plot_variance_retained failed: %s', ME.message);
end

try
    pme.plot_scree_plot(model, outdir);
catch ME
    warning('[pme.report] plot_scree_plot failed: %s', ME.message);
end

if rep.nmse.enable
    try
        pme.plot_nmse_by_source(rep, outdir);
    catch ME
        warning('[pme.report] plot_nmse_by_source failed: %s', ME.message);
    end

    try
        pme.plot_variance_by_source(rep, outdir);
    catch ME
        warning('[pme.report] plot_variance_by_source failed: %s', ME.message);
    end
end

try
    pme.plot_modes(model, outdir, min(3, nconf));
catch ME
    warning('[pme.report] plot_modes failed: %s', ME.message);
end

% % legacy compatibility if someone still expects old filenames
% try
%     if exist(fullfile(outdir,'variance_retained.png'),'file')
%         copyfile(fullfile(outdir,'variance_retained.png'), fullfile(outdir,'cumvar_vars.png'));
%     end
%     if exist(fullfile(outdir,'scree_plot.png'),'file')
%         copyfile(fullfile(outdir,'scree_plot.png'), fullfile(outdir,'scree.png'));
%     end
% catch
% end
try
    pme.plot_variable_modes(model, outdir);
catch ME
    warning('[pme.report] plot_variable_modes failed: %s', ME.message);
end

save(fullfile(outdir,'report.mat'),'rep','-v7.3');

end

% ========================= Helper functions =========================

function sources = pme_build_info_sources(pos, layout, mode)
% SOURCES ORDER:
%   PME/PI:  geom (D) first, then FIELDS, then SCALARS
%   PD:      (no geom), then FIELDS, then SCALARS
%
% IMPORTANT: variables U are NEVER a source.

mode = lower(string(mode));
sources = struct('name',{},'rows',{},'type',{},'group',{},'cond',{},'nCond',{});

% (0) geom only for PME/PI
if mode ~= "pd"
    if isempty(pos.D)
        error('[pme.report][nmse] Expected geometry block D for mode=%s, but pos.D is empty.', mode);
    end
    sources(end+1).name  = "geom"; %#ok<AGROW>
    sources(end).rows    = pos.D(:)'; %#ok<AGROW>
    sources(end).type    = "geom"; %#ok<AGROW>
    sources(end).group   = "geom"; %#ok<AGROW>
    sources(end).cond    = 1; %#ok<AGROW>
    sources(end).nCond   = 1; %#ok<AGROW>
end

% (1) FIELDS first: each condition is one source
if ~isempty(pos.F) && isfield(layout,'F') && layout.F.nRows > 0
    r = pos.F(1);

    if isfield(layout.F,'items') && ~isempty(layout.F.items)
        for i=1:numel(layout.F.items)
            it = layout.F.items(i);
            nCond = it.nCond;
            nRows = it.nRows;
            K = nRows / max(nCond,1);

            for c=1:nCond
                rr = r:(r+K-1);

                if nCond > 1
                    nm = sprintf('%s(%d)', it.name, c);
                else
                    nm = sprintf('%s', it.name);
                end

                sources(end+1).name  = string(nm); %#ok<AGROW>
                sources(end).rows    = rr; %#ok<AGROW>
                sources(end).type    = "field"; %#ok<AGROW>
                sources(end).group   = string(it.name); %#ok<AGROW>
                sources(end).cond    = c; %#ok<AGROW>
                sources(end).nCond   = nCond; %#ok<AGROW>
                r = r + K;
            end
        end
    else
        sources(end+1).name  = "Field"; %#ok<AGROW>
        sources(end).rows    = pos.F(:)'; %#ok<AGROW>
        sources(end).type    = "field"; %#ok<AGROW>
        sources(end).group   = "Field"; %#ok<AGROW>
        sources(end).cond    = 1; %#ok<AGROW>
        sources(end).nCond   = 1; %#ok<AGROW>
    end
end

% (2) SCALARS second: each condition is one source
if ~isempty(pos.C) && isfield(layout,'C') && layout.C.nRows > 0
    r = pos.C(1);

    if isfield(layout.C,'items') && ~isempty(layout.C.items)
        for i=1:numel(layout.C.items)
            it = layout.C.items(i);
            for c=1:it.nCond
                if it.nCond > 1
                    nm = sprintf('%s(%d)', it.name, c);
                else
                    nm = sprintf('%s', it.name);
                end

                sources(end+1).name  = string(nm); %#ok<AGROW>
                sources(end).rows    = r; %#ok<AGROW>
                sources(end).type    = "scalar"; %#ok<AGROW>
                sources(end).group   = string(it.name); %#ok<AGROW>
                sources(end).cond    = c; %#ok<AGROW>
                sources(end).nCond   = it.nCond; %#ok<AGROW>
                r = r + 1;
            end
        end
    else
        sources(end+1).name  = "Scalar"; %#ok<AGROW>
        sources(end).rows    = pos.C(:)'; %#ok<AGROW>
        sources(end).type    = "scalar"; %#ok<AGROW>
        sources(end).group   = "Scalar"; %#ok<AGROW>
        sources(end).cond    = 1; %#ok<AGROW>
        sources(end).nCond   = 1; %#ok<AGROW>
    end
end
end

function v = block_var(Pc, rows)
if isempty(rows), v = 0; return; end
v = sum(var(Pc(rows,:), 1, 2));
end

function out = compute_field_vars(Pc, Frows, layout)
out = struct('name',{},'var',{},'nRows',{});
r = Frows(1);

if ~isfield(layout.F,'items') || isempty(layout.F.items)
    out(1).name  = "Field";
    out(1).var   = sum(var(Pc(Frows,:),1,2));
    out(1).nRows = numel(Frows);
    return;
end

for i=1:numel(layout.F.items)
    it = layout.F.items(i);
    nCond = it.nCond;
    nRows = it.nRows;
    K = nRows / max(nCond,1);

    for c=1:nCond
        rr = r:(r+K-1);
        if nCond > 1
            out(end+1).name = sprintf('%s(%d)', it.name, c); %#ok<AGROW>
        else
            out(end+1).name = sprintf('%s', it.name); %#ok<AGROW>
        end
        out(end).var   = sum(var(Pc(rr,:), 1, 2));
        out(end).nRows = numel(rr);
        r = r + K;
    end
end
end

function out = compute_scalar_vars(Pc, Crows, layout)
out = struct('name',{},'var',{},'nRows',{});
r = Crows(1);

if ~isfield(layout.C,'items') || isempty(layout.C.items)
    out(1).name  = "Scalars";
    out(1).var   = sum(var(Pc(Crows,:),1,2));
    out(1).nRows = numel(Crows);
    return;
end

for i=1:numel(layout.C.items)
    it = layout.C.items(i);
    for c=1:it.nCond
        if it.nCond > 1
            out(end+1).name = sprintf('%s(%d)', it.name, c); %#ok<AGROW>
        else
            out(end+1).name = sprintf('%s', it.name); %#ok<AGROW>
        end
        out(end).var   = sum(var(Pc(r,:), 1, 2));
        out(end).nRows = 1;
        r = r + 1;
    end
end
end

function pos = pme_report_p_blocks(model, Np, Mact)
cfg    = model.cfg;
layout = model.layout;
mode   = lower(string(cfg.mode));

pos = struct('D',[],'U',[],'F',[],'C',[]);

switch mode
    case "pme"
        pos.D = 1:layout.D.nRows;
        pos.U = (layout.D.nRows+1):(layout.D.nRows+Mact);

    case "pi"
        r = 1;
        pos.D = r:(r+layout.D.nRows-1); r = r + layout.D.nRows;
        pos.U = r:(r+Mact-1);          r = r + Mact;
        if isfield(layout,'F') && layout.F.nRows > 0
            pos.F = r:(r+layout.F.nRows-1); r = r + layout.F.nRows;
        end
        if isfield(layout,'C') && layout.C.nRows > 0
            pos.C = r:(r+layout.C.nRows-1);
        end

    case "pd"
        r = 1;
        pos.U = r:(r+Mact-1);          r = r + Mact;
        if isfield(layout,'F') && layout.F.nRows > 0
            pos.F = r:(r+layout.F.nRows-1); r = r + layout.F.nRows;
        end
        if isfield(layout,'C') && layout.C.nRows > 0
            pos.C = r:(r+layout.C.nRows-1);
        end

    otherwise
        error('Unknown mode: %s', mode);
end

clip = @(rr) rr(rr>=1 & rr<=Np);
pos.D = clip(pos.D); pos.U = clip(pos.U); pos.F = clip(pos.F); pos.C = clip(pos.C);
end

function [ninf, nphys] = pme_compute_ninf_from_layout(model)
% Your definition:
%  PME: ninf = 1 (geom only)
%  PI:  ninf = 1 + nphys
%  PD:  ninf = nphys
%
% nphys = (#field conditions) + (#scalar conditions)

cfg    = model.cfg;
layout = model.layout;
mode   = lower(string(cfg.mode));

nphys = 0;

% fields
if isfield(layout,'F') && isfield(layout.F,'items') && ~isempty(layout.F.items)
    for i=1:numel(layout.F.items)
        nphys = nphys + layout.F.items(i).nCond;
    end
elseif isfield(layout,'F') && layout.F.nRows > 0
    nphys = nphys + 1;
end

% scalars
if isfield(layout,'C') && isfield(layout.C,'items') && ~isempty(layout.C.items)
    for i=1:numel(layout.C.items)
        nphys = nphys + layout.C.items(i).nCond;
    end
elseif isfield(layout,'C') && layout.C.nRows > 0
    nphys = nphys + 1;
end

switch mode
    case "pme"
        ninf = 1;
    case "pi"
        ninf = 1 + nphys;
    case "pd"
        ninf = nphys;
    otherwise
        error('Unknown mode for ninf: %s', mode);
end
end
