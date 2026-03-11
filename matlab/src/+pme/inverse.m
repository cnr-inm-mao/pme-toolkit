function out = inverse(model, alpha, opts)
%PME_INVERSE Reconstruct P (and optionally blocks D,U,F,C) from alpha.
% out.Prec : reconstructed P
% out.blocks: reconstructed D, Ubase, F, C (Ubase with fixed vars reinserted)

arguments
    model struct
    alpha double
    opts.dbcol_for_fixed (1,1) double = model.cfg.baseline_col
    opts.Uref double = []
end

% Reconstruct centered Pc_hat in full space:
Pc_hat = (model.Zr * alpha')';     % [S x Np]? careful dims
Pc_hat = Pc_hat';                  % -> [Nembed x S]
P_hat  = Pc_hat + model.delta_m + model.P0;

% Split P_hat into blocks consistent with mode composition
out = struct();
out.Prec = P_hat;

% Now recover D/U/F/C (and Ubase with fixed vars)
blocks_hat = pme.decompose_P(P_hat, model.layout, model.cfg);

% Reinsert fixed vars into Ubase according to policy
Ubase_hat = pme_reinsert_fixed_vars(blocks_hat.Uact, model, opts);

blocks_hat.Ubase = Ubase_hat;

out.blocks = blocks_hat;
end

function Ubase = pme_reinsert_fixed_vars(Uact, model, opts)
cfg = model.cfg;
Mbase = cfg.vars.Mbase;
idxA  = cfg.vars.idx_active(:)';
idxF  = setdiff(1:Mbase, idxA);

S = size(Uact,2);
Ubase = zeros(Mbase, S);
Ubase(idxA,:) = Uact;

policy = string(cfg.vars.fixed_policy);
switch policy
    case "baseline"
        % use baseline raw values stored during fit/prepare_vars
        if ~isfield(model,'Uinfo') || ~isfield(model.Uinfo,'Ubase_baseline_raw') || isempty(model.Uinfo.Ubase_baseline_raw)
            error('Baseline fixed vars missing. Expected model.Uinfo.Ubase_baseline_raw.');
        end
        Ubase(idxF,:) = repmat(model.Uinfo.Ubase_baseline_raw(idxF), 1, S);

    case "from_ref"
        if isempty(opts.Uref)
            error('fixed_policy="from_ref" requires opts.Uref (Mbase x 1).');
        end
        Ubase(idxF,:) = repmat(opts.Uref(idxF), 1, S);

    case "from_dbcol"
        % use a DB column provided at inverse time (must be available in model.Uinfo.Ubase_from_DB)
        col = opts.dbcol_for_fixed;
        if ~isfield(model,'Uinfo') || ~isfield(model.Uinfo,'Ubase_from_DB') || isempty(model.Uinfo.Ubase_from_DB) || col > size(model.Uinfo.Ubase_from_DB,2)
            error('Ubase DB snapshot missing/insufficient in model.Uinfo.Ubase_from_DB');
        end
        Ubase(idxF,:) = repmat(model.Uinfo.Ubase_from_DB(idxF,col), 1, S);

    otherwise
        error('Unknown fixed_policy: %s', policy);
end
end
