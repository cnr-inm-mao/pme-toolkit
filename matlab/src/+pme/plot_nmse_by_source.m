function plot_nmse_by_source(rep, outdir)
%PME.PLOT_NMSE_BY_SOURCE Plot NMSE vs retained modes for each source.

if nargin < 2 || isempty(outdir)
    outdir = fullfile(pwd,'results');
end
if ~isfolder(outdir), mkdir(outdir); end

if ~isfield(rep, 'nmse') || ~isfield(rep.nmse, 'enable') || ~rep.nmse.enable
    warning('[pme.plot_nmse_by_source] NMSE data not available. Plot skipped.');
    return;
end

k = rep.nmse.k_grid(:)';
nmse_t = real(rep.nmse.nmse_t);
sources = rep.nmse.sources;
colors = pme.source_colors(sources);

fig = figure('Name','NMSE by information source','Color','w');
ax = axes(fig);
hold(ax, 'on');

for i = 1:size(nmse_t,1)
    plot(ax, k, nmse_t(i,:), 'o-', ...
        'LineWidth', 1.0, ...
        'MarkerSize', 4, ...
        'Color', colors(i,:));
end

grid(ax, 'on');
box(ax, 'on');
xlabel(ax, 'Number of retained modes, k [-]');
ylabel(ax, 'NMSE [-]');
title(ax, sprintf('NMSE by information source (%s)', upper(string(rep.mode))), ...
    'FontWeight', 'bold');
xlim(ax, [k(1), k(end)]);

labels = cell(1, numel(sources));
for i = 1:numel(sources)
    labels{i} = char(string(sources(i).name));
end

legend(ax, labels, 'Location', 'northeast', 'Interpreter', 'none');

saveas(fig, fullfile(outdir, 'nmse_by_source.png'));
close(fig);

end