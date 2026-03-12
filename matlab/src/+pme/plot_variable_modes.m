function plot_variable_modes(model, outdir)
%PME.PLOT_VARIABLE_MODES Plot retained variable-mode components.
%
% For each retained mode j = 1..nconf:
%   y = abs(component) / max(abs(component))
%
% Output:
%   variable_modes_normalized.png

if nargin < 2 || isempty(outdir)
    outdir = fullfile(pwd,'results');
end
if ~isfolder(outdir), mkdir(outdir); end

cfg = model.cfg;
mode = lower(string(cfg.mode));

if isfield(model,'Uinfo') && isfield(model.Uinfo,'idx_active') && ~isempty(model.Uinfo.idx_active)
    Mact = numel(model.Uinfo.idx_active);
else
    Mact = cfg.vars.Mbase;
end

Np = size(model.Zr,1);
pos = local_p_blocks(model, Np, Mact);

if isempty(pos.U)
    warning('[pme.plot_variable_modes] Variable block U is empty. Plot skipped.');
    return;
end

Z = model.Zr;
nconf = size(Z,2);
U_modes = Z(pos.U, 1:nconf);

fig = figure('Name','Variable modes','Color','w');

for j = 1:nconf
    ax = subplot(nconf,1,j); 
    hold(ax, 'on');

    uj = abs(U_modes(:,j));
    den = max(uj);
    if den < eps
        uj = zeros(size(uj));
    else
        uj = uj / den;
    end

    plot(ax, 1:Mact, uj, 'o-', ...
        'Color', [0 0.4470 0.7410], ...
        'LineWidth', 0.8, ...
        'MarkerSize', 3);

    xlim(ax, [1, Mact]);
    ylim(ax, [0, 1.05]);
    grid(ax, 'on');
    box(ax, 'on');
    ylabel(ax, sprintf('m_{%d}', j), 'Interpreter', 'tex');

    if j < nconf
        set(ax, 'XTickLabel', []);
    else
        xlabel(ax, 'Eigenvector variable components [-]');
    end
end

sgtitle(sprintf('Normalized absolute variable participation per retained mode (%s)', ...
    upper(mode)), ...
    'FontWeight', 'bold', ...
    'FontSize', 11, ...
    'Interpreter', 'none');

saveas(fig, fullfile(outdir, 'variable_modes_normalized.png'));
close(fig);

end

function pos = local_p_blocks(model, Np, Mact)
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
        pos.U = r:(r+Mact-1);           r = r + Mact;
        if isfield(layout,'F') && layout.F.nRows > 0
            pos.F = r:(r+layout.F.nRows-1); r = r + layout.F.nRows;
        end
        if isfield(layout,'C') && layout.C.nRows > 0
            pos.C = r:(r+layout.C.nRows-1);
        end

    case "pd"
        r = 1;
        pos.U = r:(r+Mact-1);           r = r + Mact;
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
pos.D = clip(pos.D);
pos.U = clip(pos.U);
pos.F = clip(pos.F);
pos.C = clip(pos.C);
end