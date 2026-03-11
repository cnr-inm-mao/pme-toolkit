function blocks = decompose_P(P, layout, cfg)
% Decompose P into blocks consistent with cfg.mode composition (not DB rows)
mode = lower(string(cfg.mode));
Mact = numel(cfg.vars.idx_active);

blocks = struct();
ptr = 1;

switch mode
    case "pme"
        blocks.D = P(ptr:ptr+layout.D.nRows-1, :); ptr = ptr+layout.D.nRows;
        blocks.Uact = P(ptr:ptr+Mact-1, :); ptr = ptr+Mact;
        blocks.F = [];
        blocks.C = [];

    case "pi"
        blocks.D = P(ptr:ptr+layout.D.nRows-1, :); ptr = ptr+layout.D.nRows;
        blocks.Uact = P(ptr:ptr+Mact-1, :); ptr = ptr+Mact;

        if layout.F.nRows > 0
            blocks.F = P(ptr:ptr+layout.F.nRows-1,:); ptr = ptr+layout.F.nRows;
        else
            blocks.F = [];
        end
        if layout.C.nRows > 0
            blocks.C = P(ptr:ptr+layout.C.nRows-1,:); ptr = ptr+layout.C.nRows;
        else
            blocks.C = [];
        end

    case "pd"
        blocks.D = []; % not present in P
        blocks.Uact = P(ptr:ptr+Mact-1, :); ptr = ptr+Mact;

        if layout.F.nRows > 0
            blocks.F = P(ptr:ptr+layout.F.nRows-1,:); ptr = ptr+layout.F.nRows;
        else
            blocks.F = [];
        end
        if layout.C.nRows > 0
            blocks.C = P(ptr:ptr+layout.C.nRows-1,:); ptr = ptr+layout.C.nRows;
        else
            blocks.C = [];
        end

    otherwise
        error('Unknown mode');
end
end
