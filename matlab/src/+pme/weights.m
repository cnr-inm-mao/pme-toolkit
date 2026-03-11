function [W, stats] = weights(delta, layout, cfg, Uinfo, blocks)
%PME_WEIGHTS Build block-diagonal weights consistent with "ninf as #information".
%
% Idea:
% - Each INFORMATION contributes ~1 to trace(W*Cov) => sum(eigs) ~ ninf.
% - Geometry D counts as 1 info (when present in P).
% - Each FIELD condition counts as 1 info (weight per condition block).
% - Each SCALAR (and each scalar condition) counts as 1 info (weight per row).
% - Variables U weight is usually 0 in PI/PD/PME (as in your scripts).

mode = lower(string(cfg.mode));

Dlen = layout.D.nRows;
Ulen = Uinfo.Mact;
Flen = size(blocks.F,1);
Clen = size(blocks.C,1);

% Helper: safe inverse
invv = @(x) 1/max(x, eps);

switch mode
    case "pme"
        % P=[D;U]
        N = Dlen + Ulen;
        W = zeros(N,N);

        % D = 1 information
        varD = sum(var(delta(1:Dlen,:),1,2));
        wD = invv(varD);
        W(1:Dlen,1:Dlen) = wD * eye(Dlen);

        % U usually not weighted in PME PCA (keep 0)
        % If you ever want it: set wU = invv(sum(var(...)))
        wU = 0;
        if wU > 0
            W(Dlen+1:Dlen+Ulen, Dlen+1:Dlen+Ulen) = wU * eye(Ulen);
        end

        stats = pack_stats(mode, Dlen, Ulen, Flen, Clen, 1, 0, 0);

    case "pi"
        % P=[D;U;F;C]
        N = Dlen + Ulen + Flen + Clen;
        W = zeros(N,N);

        % --- D = 1 information ---
        ptr = 1;
        varD = sum(var(delta(ptr:ptr+Dlen-1,:),1,2)); ptr = ptr + Dlen;
        wD = invv(varD);
        W(1:Dlen,1:Dlen) = wD * eye(Dlen);

        % --- U typically 0 ---
        % still advance ptr across U block in delta indexing
        varU = sum(var(delta(ptr:ptr+Ulen-1,:),1,2)); %#ok<NASGU>
        ptrU0 = ptr;
        ptr = ptr + Ulen;
        wU = 0;
        if wU > 0
            W(Dlen+1:Dlen+Ulen, Dlen+1:Dlen+Ulen) = wU * eye(Ulen);
        end

        % --- F: 1 info per field condition ---
        [WF, nFinfo, ptr] = build_WF(delta, ptr, Dlen+Ulen, layout, Flen);
        if ~isempty(WF)
            a = Dlen+Ulen+1; b = Dlen+Ulen+Flen;
            W(a:b, a:b) = WF;
        end

        % --- C: 1 info per scalar condition (row-by-row) ---
        [WC, nCinfo] = build_WC(delta, ptr, Dlen+Ulen+Flen, layout, Clen);
        if ~isempty(WC)
            a = Dlen+Ulen+Flen+1; b = Dlen+Ulen+Flen+Clen;
            W(a:b, a:b) = WC;
        end

        stats = pack_stats(mode, Dlen, Ulen, Flen, Clen, 1, nFinfo, nCinfo);
        stats.ptrU0 = ptrU0; % debug

    case "pd"
        % P=[U;F;C]
        N = Ulen + Flen + Clen;
        W = zeros(N,N);

        % --- U weight 0 (physics-driven) ---
        wU = 0;
        if wU > 0
            W(1:Ulen,1:Ulen) = wU * eye(Ulen);
        end

        ptr = 1 + Ulen;

        % --- F: 1 info per field condition ---
        [WF, nFinfo, ptr] = build_WF(delta, ptr, Ulen, layout, Flen);
        if ~isempty(WF)
            a = Ulen+1; b = Ulen+Flen;
            W(a:b, a:b) = WF;
        end

        % --- C: 1 info per scalar condition ---
        [WC, nCinfo] = build_WC(delta, ptr, Ulen+Flen, layout, Clen);
        if ~isempty(WC)
            a = Ulen+Flen+1; b = Ulen+Flen+Clen;
            W(a:b, a:b) = WC;
        end

        if Flen==0
            warning('PD-PME with no F: physics-driven DR limited by C.');
        end

        stats = pack_stats(mode, Dlen, Ulen, Flen, Clen, 0, nFinfo, nCinfo);

    otherwise
        error('Unknown mode: %s', mode);
end
end

% ================= helpers =================

function [WF, nFinfo, ptr_out] = build_WF(delta, ptr_in, offset, layout, Flen)
% Build weights for F block: 1 info per field condition (block per condition)
% Returns:
%  WF: [Flen x Flen] diagonal (constant per condition block)
%  nFinfo: number of field informations
%  ptr_out: updated ptr in delta indexing

WF = [];
nFinfo = 0;
ptr = ptr_in;

if Flen <= 0
    ptr_out = ptr;
    return;
end

WF = zeros(Flen, Flen);

if isfield(layout,'F') && isfield(layout.F,'items') && ~isempty(layout.F.items)
    local = 1;
    for i=1:numel(layout.F.items)
        it = layout.F.items(i);
        nCond = it.nCond;
        nRows = it.nRows;
        K = nRows / max(nCond,1);

        for c=1:nCond
            rr_delta = ptr:(ptr+K-1);
            varBlock = sum(var(delta(rr_delta,:),1,2));
            w = 1/max(varBlock, eps);

            rr_W = local:(local+K-1);
            WF(rr_W, rr_W) = w * eye(K);

            ptr = ptr + K;
            local = local + K;
            nFinfo = nFinfo + 1;
        end
    end
else
    % fallback: treat whole F as 1 info
    varF = sum(var(delta(ptr:ptr+Flen-1,:),1,2));
    wF = 1/max(varF, eps);
    WF(:,:) = wF * eye(Flen);
    ptr = ptr + Flen;
    nFinfo = 1;
end

ptr_out = ptr;
end

function [WC, nCinfo] = build_WC(delta, ptr_in, offset, layout, Clen)
% Build weights for C block: 1 info per scalar condition (row-by-row)
% Returns WC [Clen x Clen] diagonal.

WC = [];
nCinfo = 0;

if Clen <= 0
    return;
end

WC = zeros(Clen, Clen);

if isfield(layout,'C') && isfield(layout.C,'items') && ~isempty(layout.C.items)
    ptr = ptr_in;
    local = 1;
    for i=1:numel(layout.C.items)
        it = layout.C.items(i);
        for c=1:it.nCond
            rr_delta = ptr; % one row in C
            v = var(delta(rr_delta,:),1,2);
            w = 1/max(v, eps);

            WC(local, local) = w;

            ptr = ptr + 1;
            local = local + 1;
            nCinfo = nCinfo + 1;
        end
    end
else
    % fallback: treat whole C as 1 info
    varC = sum(var(delta(ptr_in:ptr_in+Clen-1,:),1,2));
    wC = 1/max(varC, eps);
    WC(:,:) = wC * eye(Clen);
    nCinfo = 1;
end
end

function stats = pack_stats(mode, Dlen, Ulen, Flen, Clen, nDinfo, nFinfo, nCinfo)
stats = struct();
stats.mode = mode;
stats.sizes = struct('D',Dlen,'U',Ulen,'F',Flen,'C',Clen);
stats.ninfo = struct('D',nDinfo,'F',nFinfo,'C',nCinfo,'total',nDinfo+nFinfo+nCinfo);
end
