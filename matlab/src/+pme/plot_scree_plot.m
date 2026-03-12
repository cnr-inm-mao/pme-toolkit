
function plot_scree_plot(model, outdir)
%PME.PLOT_SCREE_PLOT Plot scree of eigenvalues.
%
% Shows eigenvalues up to Mact.

if nargin < 2 || isempty(outdir)
    outdir = fullfile(pwd,'results');
end
if ~isfolder(outdir), mkdir(outdir); end

L = model.L_full(:);
nconf = model.sizes.nconf;
cfg = model.cfg;

if isempty(L)
    warning('[pme.plot_scree_plot] No eigenvalues available. Plot skipped.');
    return;
end

% determine Mact
if isfield(model,'Uinfo') && isfield(model.Uinfo,'idx_active') && ~isempty(model.Uinfo.idx_active)
    Mact = numel(model.Uinfo.idx_active);
else
    Mact = cfg.vars.Mbase;
end

Mplot = min(Mact, numel(L));
x = 1:Mplot;

fig = figure('Name','Scree plot','Color','w');
ax = axes(fig);
hold(ax,'on');

plot(ax, x, L(1:Mplot), 'o-', ...
    'LineWidth', 1.1, ...
    'MarkerSize', 4);

plot(ax, [nconf nconf], ...
    [min(L(1:Mplot)) max(L(1:Mplot))], ...
    ':', 'LineWidth', 1.0);

grid(ax,'on');
box(ax,'on');

xlabel(ax,'Mode index [-]');
ylabel(ax,'Eigenvalue \lambda_j [-]');

title(ax, sprintf('Eigenvalue spectrum (%s)', upper(string(cfg.mode))), ...
    'FontWeight','bold');

xlim(ax,[1 Mplot]);

legend(ax, {'\lambda_j','selected N'}, ...
    'Location','northeast');

saveas(fig, fullfile(outdir,'scree_plot.png'));
close(fig);

end