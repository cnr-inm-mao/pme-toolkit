function colors = source_colors(sources)
%PME.SOURCE_COLORS Colorblind-safe colors for information sources.
%
% Rules:
% - geometry: fixed dark gray
% - fields:   cool families
% - scalars:  warm families
% - multiple conditions of same group: same family, different shades

n = numel(sources);
colors = zeros(n,3);

if n == 0
    return;
end

% Colorblind-safe base palette (Okabe-Ito inspired)
geom_color = [0.20 0.20 0.20];

field_bases = [
    0.00 0.45 0.70  % blue
    0.00 0.62 0.45  % bluish green / teal
    0.35 0.55 0.85  % lighter blue
    0.50 0.40 0.75  % muted purple
];

scalar_bases = [
    0.90 0.60 0.00  % orange
    0.80 0.40 0.00  % dark orange
    0.80 0.47 0.65  % reddish purple
    0.65 0.37 0.15  % brown
];

field_groups = strings(0);
scalar_groups = strings(0);

for i = 1:n
    typ = lower(string(sources(i).type));
    grp = string(sources(i).group);
    cond = double(sources(i).cond);
    nCond = double(sources(i).nCond);

    switch typ
        case "geom"
            colors(i,:) = geom_color;

        case "field"
            idx = find(field_groups == grp, 1);
            if isempty(idx)
                field_groups(end+1) = grp; %#ok<AGROW>
                idx = numel(field_groups);
            end
            base = field_bases(mod(idx-1, size(field_bases,1)) + 1, :);
            colors(i,:) = local_shade(base, cond, nCond);

        case "scalar"
            idx = find(scalar_groups == grp, 1);
            if isempty(idx)
                scalar_groups(end+1) = grp; %#ok<AGROW>
                idx = numel(scalar_groups);
            end
            base = scalar_bases(mod(idx-1, size(scalar_bases,1)) + 1, :);
            colors(i,:) = local_shade(base, cond, nCond);

        otherwise
            colors(i,:) = [0 0 0];
    end
end

end

function c = local_shade(base, cond, nCond)
% Generate shades that remain distinguishable for colorblind users.
% cond=1 -> darker/base, last cond -> lighter but still saturated.

if nCond <= 1
    c = base;
    return;
end

% Blend with white in a limited range to keep contrast.
t = 0.00 + 0.35 * (cond-1) / max(nCond-1, 1);
c = (1-t) * base + t * [1 1 1];

% Slight clamp to avoid too pale colors
c = min(max(c, 0), 0.95);
end