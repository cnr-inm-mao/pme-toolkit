function cfg = defaults(cfg)

if ~isfield(cfg,'mode'), cfg.mode = "pme"; end
if ~isfield(cfg,'CI'), cfg.CI = 0.99; end
if ~isfield(cfg,'baseline_col'), cfg.baseline_col = 1; end

% geom
assert(isfield(cfg,'geom') && isfield(cfg.geom,'Jdir') && isfield(cfg.geom,'patches'), ...
    'cfg.geom.Jdir and cfg.geom.patches are required');
assert(any(cfg.geom.Jdir == [2,3]), 'cfg.geom.Jdir must be 2 or 3');

% vars
assert(isfield(cfg,'vars') && isfield(cfg.vars,'Mbase') && isfield(cfg.vars,'idx_active'), ...
    'cfg.vars.Mbase and cfg.vars.idx_active required');
if ~isfield(cfg.vars,'fixed_policy'), cfg.vars.fixed_policy = "baseline"; end
if ~isfield(cfg.vars,'Urange'), cfg.vars.Urange = []; end
if ~isfield(cfg.vars,'use_db_range_if_missing'), cfg.vars.use_db_range_if_missing = true; end

% phys (optional)
if ~isfield(cfg,'phys'), cfg.phys = struct(); end
if ~isfield(cfg.phys,'fields'), cfg.phys.fields = struct([]); end
if ~isfield(cfg.phys,'scalars'), cfg.phys.scalars = struct([]); end

% filters
if ~isfield(cfg,'filters'), cfg.filters = struct(); end
if ~isfield(cfg.filters,'remove_nan'), cfg.filters.remove_nan = true; end
if ~isfield(cfg.filters,'goal'), cfg.filters.goal = struct('enable',false); end

end
