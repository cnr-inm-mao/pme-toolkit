function validate_physics_config(cfg)
%PME.VALIDATE_PHYSICS_CONFIG Require physical inputs for PI-PME and PD-PME.
% Standard PME may omit cfg.phys. Physics-aware modes must declare at least
% one field or scalar, so a missing configuration cannot silently change the
% intended reduction method.

if ~isfield(cfg,'mode'), return; end
mode = lower(string(cfg.mode));
if ~any(mode == ["pi", "pd"]), return; end

hasPhysics = isfield(cfg,'phys') && isstruct(cfg.phys) && isscalar(cfg.phys) && ...
    ((isfield(cfg.phys,'fields') && ~isempty(cfg.phys.fields)) || ...
     (isfield(cfg.phys,'scalars') && ~isempty(cfg.phys.scalars)));

if ~hasPhysics
    error('pme:MissingPhysics', ...
        ['mode=''%s'' requires at least one physical field or scalar in ' ...
         'cfg.phys.fields or cfg.phys.scalars. Use mode=''pme'' for geometry-only PME.'], ...
        mode);
end

end
