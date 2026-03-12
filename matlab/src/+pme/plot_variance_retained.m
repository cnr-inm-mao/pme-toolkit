function plot_variance_retained(model, outdir)
%PME.PLOT_VARIANCE_RETAINED Plot retained variance curve up to Mact.
%
% Output:
%   variance_retained.png
%
% Conventions:
% - x-axis goes up to kmax = min(Mact, numel(L))
% - shaded area from 95% to 100%
% - horizontal line at 99%
% - vertical line at nconf
% - no marker at Mact

if nargin < 2 || isempty(outdir)
    outdir = fullfile(pwd,'results');
end
if ~isfolder(outdir), mkdir(outdir); end

L = model.L_full(:);
nconf = model.sizes.nconf;
cfg = model.cfg;

if isfield(model,'Uinfo') && isfield(model.Uinfo,'idx_active') && ~isempty(model.Uinfo.idx_active)
    Mact = numel(model.Uinfo.idx_active);
else
    Mact = cfg.vars.Mbase;
end

ninf = local_compute_ninf(model);
kmax = min(Mact, numel(L));

if kmax < 1
    warning('[pme.plot_variance_retained] No eigenvalues available. Plot skipped.');
    return;
end

cumPct = 100 * cumsum(L(1:kmax)) / max(double(ninf), eps);
x = 1:kmax;

fig = figure('Name','Retained variance','Color','w');
ax = axes(fig);
hold(ax, 'on');

% shaded area 95-100
h0 = patch(ax, [1 kmax kmax 1], [95 95 100 100], [0.90 0.90 0.90], ...
    'EdgeColor', 'none', 'FaceAlpha', 0.6);

h1 = plot(ax, x, cumPct, 'o-', 'LineWidth', 1.0, 'MarkerSize', 4);
h2 = plot(ax, [1 kmax], [99 99], '--', 'LineWidth', 1.0);

if nconf <= kmax
    h3 = plot(ax, [nconf nconf], [0 100], ':', 'LineWidth', 1.0);
else
    h3 = plot(ax, [kmax kmax], [0 100], ':', 'LineWidth', 1.0);
end

grid(ax, 'on');
box(ax, 'on');
xlabel(ax, 'Number of retained modes, k [-]');
ylabel(ax, 'Retained variance [%]');
title(ax, sprintf('Retained variance (%s)', upper(string(cfg.mode))), ...
    'FontWeight', 'bold');
xlim(ax, [1 kmax]);
ylim(ax, [0 100]);

legend(ax, [h0 h1 h2 h3], ...
    {'95% threshold', 'cumulative', '99% threshold', 'selected N'}, ...
    'Location', 'southeast');

saveas(fig, fullfile(outdir, 'variance_retained.png'));
close(fig);

end

function ninf = local_compute_ninf(model)
cfg    = model.cfg;
layout = model.layout;
mode   = lower(string(cfg.mode));

nphys = 0;

if isfield(layout,'F') && isfield(layout.F,'items') && ~isempty(layout.F.items)
    for i=1:numel(layout.F.items)
        nphys = nphys + layout.F.items(i).nCond;
    end
elseif isfield(layout,'F') && isfield(layout.F,'nRows') && layout.F.nRows > 0
    nphys = nphys + 1;
end

if isfield(layout,'C') && isfield(layout.C,'items') && ~isempty(layout.C.items)
    for i=1:numel(layout.C.items)
        nphys = nphys + layout.C.items(i).nCond;
    end
elseif isfield(layout,'C') && isfield(layout.C,'nRows') && layout.C.nRows > 0
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
        error('Unknown mode: %s', mode);
end
end