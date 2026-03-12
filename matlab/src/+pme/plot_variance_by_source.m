function plot_variance_by_source(rep, outdir)
%PME.PLOT_VARIANCE_BY_SOURCE Plot retained variance vs retained modes.

if nargin < 2 || isempty(outdir)
    outdir = fullfile(pwd,'results');
end
if ~isfolder(outdir), mkdir(outdir); end

if ~isfield(rep, 'nmse') || ~isfield(rep.nmse, 'enable') || ~rep.nmse.enable
    warning('[pme.plot_variance_by_source] NMSE data not available. Plot skipped.');
    return;
end

k = rep.nmse.k_grid(:)';
var_t = real(rep.nmse.var_t);
sources = rep.nmse.sources;
colors = pme.source_colors(sources);

fig = figure('Name','Retained variance by information source','Color','w');
ax = axes(fig);
hold(ax, 'on');

for i = 1:size(var_t,1)
    plot(ax, k, var_t(i,:), 'o-', ...
        'LineWidth', 1.0, ...
        'MarkerSize', 4, ...
        'Color', colors(i,:));
end

grid(ax, 'on');
box(ax, 'on');
xlabel(ax, 'Number of retained modes, k [-]');
ylabel(ax, 'Retained variance [-]');
title(ax, sprintf('Retained variance by information source (%s)', upper(string(rep.mode))), ...
    'FontWeight', 'bold');
xlim(ax, [k(1), k(end)]);
ylim(ax, [0, 1.05]);

labels = cell(1, numel(sources));
for i = 1:numel(sources)
    labels{i} = char(string(sources(i).name));
end

legend(ax, labels, 'Location', 'southeast', 'Interpreter', 'none');

saveas(fig, fullfile(outdir, 'variance_by_source.png'));
close(fig);

end