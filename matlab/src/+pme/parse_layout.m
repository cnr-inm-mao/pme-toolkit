function layout = parse_layout(cfg)
% Compute row offsets for D, Ubase, F, C based on cfg (contracted ordering)

layout = struct();
layout.geom = cfg.geom;
layout.vars = cfg.vars;
layout.phys = cfg.phys;

Jdir = cfg.geom.Jdir;
patches = cfg.geom.patches;
Kpatch = arrayfun(@(p) p.K, patches);
Ktot = sum(Kpatch);

layout.D.nRows = Jdir * Ktot;

layout.Ubase.nRows = cfg.vars.Mbase;

% Physics: fields then scalars; within each item conditions contiguous
layout.F.items = cfg.phys.fields;
layout.C.items = cfg.phys.scalars;

layout.F.nRows = 0;
for i=1:numel(layout.F.items)
    item = layout.F.items(i);
    K = pme_field_K(item);
    layout.F.items(i).nRows = item.nCond * K;
    layout.F.nRows = layout.F.nRows + layout.F.items(i).nRows;
end

layout.C.nRows = 0;
for i=1:numel(layout.C.items)
    item = layout.C.items(i);
    layout.C.items(i).nRows = item.nCond;
    layout.C.nRows = layout.C.nRows + item.nCond;
end

% Offsets in DB row space
r0 = 0;
layout.D.rows = (r0+1):(r0+layout.D.nRows); r0 = r0 + layout.D.nRows;
layout.Ubase.rows = (r0+1):(r0+layout.Ubase.nRows); r0 = r0 + layout.Ubase.nRows;
layout.F.rows = (r0+1):(r0+layout.F.nRows); r0 = r0 + layout.F.nRows;
layout.C.rows = (r0+1):(r0+layout.C.nRows); r0 = r0 + layout.C.nRows;

layout.totalRows = r0;
end

function K = pme_field_K(item)
if ~isfield(item,'disc') || isempty(item.disc)
    error('Field item requires item.disc');
end
if isfield(item.disc,'K') && ~isempty(item.disc.K)
    K = item.disc.K;
elseif isfield(item.disc,'patches') && ~isempty(item.disc.patches)
    K = sum(arrayfun(@(p) p.K, item.disc.patches));
else
    error('Field discretization must define disc.K or disc.patches');
end
end
