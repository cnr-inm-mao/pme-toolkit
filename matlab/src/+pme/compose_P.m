function P = compose_P(D, Uact, F, C, cfg)
mode = lower(string(cfg.mode));

hasF = ~isempty(F);
hasC = ~isempty(C);

switch mode
    case "pme"
        P = [D; Uact];

    case "pi"
        P = [D; Uact];
        if hasF, P = [P; F]; end
        if hasC, P = [P; C]; end

    case "pd"
        % Your definition: P=[U;F;C] (U must exist for backmapping)
        P = [Uact];
        if hasF, P = [P; F]; end
        if hasC, P = [P; C]; end

        if ~hasF
            warning(['PD-PME without fields F: dimensionality reduction will be limited by rank of scalars C. ' ...
                     'This is usually not desired.']);
        end

    otherwise
        error('Unknown mode: %s', mode);
end
end
