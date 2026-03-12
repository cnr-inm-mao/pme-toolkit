function plot_modes(model, outdir, nModes)
%PME.PLOT_MODES Plot first geometric modes as baseline +/- scaled mode.
%
% Outputs:
%   mode_01.png
%   mode_02.png
%   mode_03.png
%
% Features:
% - same axis limits across the first nModes
% - 2D plot if Jdir == 2
% - 3D plot if Jdir == 3
% - smaller markers for readability

if nargin < 2 || isempty(outdir)
    outdir = fullfile(pwd,'results');
end
if nargin < 3 || isempty(nModes)
    nModes = 3;
end
if ~isfolder(outdir), mkdir(outdir); end

cfg = model.cfg;
mode = lower(string(cfg.mode));

if mode == "pd"
    % PD-PME has no geometry block in the embedded vector; geometric modes are not available.
    return;
end

if ~isfield(cfg, 'geom') || ~isfield(cfg.geom, 'Jdir') || ~isfield(cfg.geom, 'patches')
    warning('[pme.plot_modes] Geometry metadata missing. Plot skipped.');
    return;
end

Jdir = cfg.geom.Jdir;
patches = cfg.geom.patches;
Kpatch = arrayfun(@(p) p.K, patches);
Ktot = sum(Kpatch);
Drows = Jdir * Ktot;

if ~isfield(model, 'P0') || numel(model.P0) < Drows
    warning('[pme.plot_modes] model.P0 does not contain enough geometry rows. Plot skipped.');
    return;
end

if ~isfield(model, 'Zr') || isempty(model.Zr)
    warning('[pme.plot_modes] model.Zr missing. Plot skipped.');
    return;
end

nModes = min([nModes, size(model.Zr,2)]);
if nModes < 1
    return;
end

D0 = model.P0(1:Drows);

% -------------------------------------------------
% Precompute scales and global axis limits
% -------------------------------------------------
scales = zeros(nModes,1);

if Jdir == 2
    xmin = +inf; xmax = -inf;
    ymin = +inf; ymax = -inf;
elseif Jdir == 3
    xmin = +inf; xmax = -inf;
    ymin = +inf; ymax = -inf;
    zmin = +inf; zmax = -inf;
else
    warning('[pme.plot_modes] Unsupported Jdir=%d. Plot skipped.', Jdir);
    return;
end

for j = 1:nModes
    phi = model.Zr(1:Drows, j);
    scales(j) = local_mode_sigma_scale(model, j);

    offset = 0;
    for ip = 1:numel(Kpatch)
        K = Kpatch(ip);
        rows = offset + (1:(Jdir*K));

        G0 = reshape(D0(rows), [K, Jdir]);
        Gp = reshape(D0(rows) + scales(j)*phi(rows), [K, Jdir]);
        Gm = reshape(D0(rows) - scales(j)*phi(rows), [K, Jdir]);

        Gall = [G0; Gp; Gm];

        xmin = min(xmin, min(Gall(:,1)));
        xmax = max(xmax, max(Gall(:,1)));
        ymin = min(ymin, min(Gall(:,2)));
        ymax = max(ymax, max(Gall(:,2)));

        if Jdir == 3
            zmin = min(zmin, min(Gall(:,3)));
            zmax = max(zmax, max(Gall(:,3)));
        end

        offset = offset + Jdir*K;
    end
end

% small padding
xpad = 0.03 * max(xmax - xmin, eps);
ypad = 0.03 * max(ymax - ymin, eps);
xmin = xmin - xpad; xmax = xmax + xpad;
ymin = ymin - ypad; ymax = ymax + ypad;

if Jdir == 3
    zpad = 0.03 * max(zmax - zmin, eps);
    zmin = zmin - zpad; zmax = zmax + zpad;
end

% -------------------------------------------------
% Plot each mode with same axis limits
% -------------------------------------------------
for j = 1:nModes
    phi = model.Zr(1:Drows, j);
    scale = scales(j);

    fig = figure('Name', sprintf('Mode %02d', j), 'Color', 'w');
    ax = axes(fig);
    hold(ax, 'on');

    offset = 0;
    for ip = 1:numel(Kpatch)
        K = Kpatch(ip);
        rows = offset + (1:(Jdir*K));

        G0 = reshape(D0(rows), [K, Jdir]);
        Gp = reshape(D0(rows) + scale*phi(rows), [K, Jdir]);
        Gm = reshape(D0(rows) - scale*phi(rows), [K, Jdir]);

        if Jdir == 3
            scatter3(ax, G0(:,1), G0(:,2), G0(:,3), 5, 'k', 'filled');
            scatter3(ax, Gp(:,1), Gp(:,2), Gp(:,3), 4, 'b');
            scatter3(ax, Gm(:,1), Gm(:,2), Gm(:,3), 4, 'r');
        else
            plot(ax, G0(:,1), G0(:,2), 'k.-', 'LineWidth', 0.8, 'MarkerSize', 5);
            plot(ax, Gp(:,1), Gp(:,2), 'b.-', 'LineWidth', 0.8, 'MarkerSize', 4);
            plot(ax, Gm(:,1), Gm(:,2), 'r.-', 'LineWidth', 0.8, 'MarkerSize', 4);
        end

        offset = offset + Jdir*K;
    end

    grid(ax, 'on');
    box(ax, 'on');
    axis(ax, 'equal');
    xlabel(ax, 'x');
    ylabel(ax, 'y');
    xlim(ax, [xmin xmax]);
    ylim(ax, [ymin ymax]);

    if Jdir == 3
        zlabel(ax, 'z');
        zlim(ax, [zmin zmax]);
        view(ax, 3);
    end

    title(ax, sprintf('Geometric mode %d', j), 'FontWeight', 'bold');
    if Jdir == 3
        legend(ax, {'baseline', '+ mode', '- mode'}, 'Location', 'northeast');
    else
        legend(ax, {'baseline', '+ mode', '- mode'}, 'Location', 'best');
    end

    saveas(fig, fullfile(outdir, sprintf('mode_%02d.png', j)));
    close(fig);
end

end

function scale = local_mode_sigma_scale(model, j)
% Use +/- 3*sqrt(lambda_j) as modal amplitude if available.

if isfield(model,'Lr') && ~isempty(model.Lr) && numel(model.Lr) >= j
    lam = real(model.Lr(j));
elseif isfield(model,'L_full') && ~isempty(model.L_full) && numel(model.L_full) >= j
    lam = real(model.L_full(j));
else
    error('No eigenvalues available to scale geometric modes.');
end

lam = max(lam, 0);
scale = 3.0 * sqrt(lam);
end