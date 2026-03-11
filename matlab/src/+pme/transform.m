function alpha = transform(model, DB_or_blocks)
%PME_TRANSFORM Map a DB (or already sliced blocks) into alpha coordinates.
% alpha = transform(model, DB)

if isnumeric(DB_or_blocks)
    blocks = slice(DB_or_blocks, model.layout);
else
    blocks = DB_or_blocks;
end

[Uact, ~] = pme.prepare_vars(blocks.Ubase, model.cfg, blocks);
P = pme.compose_P(blocks.D, Uact, blocks.F, blocks.C, model.cfg);

delta = P - model.P0;
Pc    = delta - model.delta_m;

% alpha in reduced basis
alpha = (Pc' * model.W * model.Zr);  % [S x nconf]
end
