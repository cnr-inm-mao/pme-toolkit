function plot_variance_retained(model, outdir)
%PME.PLOT_VARIANCE_RETAINED Plot retained weighted construction variance.
%
% Output:
%   variance_retained.png
%
% Conventions:
% - x-axis includes the selected dimension and at least Mact when resolved
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

total_variance = pme.total_variance(model);
kmax = min(max(Mact, nconf), numel(L));

if kmax < 1
    warning('[pme.plot_variance_retained] No eigenvalues available. Plot skipped.');
    return;
end

cumPct = 100 * cumsum(L(1:kmax)) / total_variance;
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
if kmax == 1, xlim(ax, [0.5 1.5]); else, xlim(ax, [1 kmax]); end
ylim(ax, [0 100]);

legend(ax, [h0 h1 h2 h3], ...
    {'95% threshold', 'cumulative', '99% threshold', 'selected N'}, ...
    'Location', 'southeast');

saveas(fig, fullfile(outdir, 'variance_retained.png'));
close(fig);

end
