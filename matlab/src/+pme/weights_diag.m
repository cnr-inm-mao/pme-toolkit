function [w, stats] = weights_diag(delta, layout, cfg, Uinfo, blocks)
%PME.WEIGHTS_DIAG Build a weight vector without allocating a dense metric.
% Geometry, each field condition and each scalar condition count as one
% information source. Native design-variable rows always have weight zero.

mode = lower(string(cfg.mode));
Dlen = layout.D.nRows;
Ulen = Uinfo.Mact;
Flen = size(blocks.F, 1);
Clen = size(blocks.C, 1);
nDinfo = double(mode ~= "pd");
nFinfo = 0;
nCinfo = 0;

switch mode
    case "pme"
        w = zeros(Dlen + Ulen, 1);
        w(1:Dlen) = inverse_variance(delta(1:Dlen, :));
    case {"pi", "pd"}
        if mode == "pi"
            w = zeros(Dlen + Ulen + Flen + Clen, 1);
            w(1:Dlen) = inverse_variance(delta(1:Dlen, :));
            ptr = Dlen + Ulen + 1;
        else
            w = zeros(Ulen + Flen + Clen, 1);
            ptr = Ulen + 1;
        end
        if Flen > 0
            if isfield(layout.F, 'items') && ~isempty(layout.F.items)
                for i = 1:numel(layout.F.items)
                    item = layout.F.items(i);
                    K = item.nRows / max(item.nCond, 1);
                    for c = 1:item.nCond
                        rows = ptr:(ptr + K - 1);
                        w(rows) = inverse_variance(delta(rows, :));
                        ptr = ptr + K;
                        nFinfo = nFinfo + 1;
                    end
                end
            else
                rows = ptr:(ptr + Flen - 1);
                w(rows) = inverse_variance(delta(rows, :));
                ptr = ptr + Flen;
                nFinfo = 1;
            end
        end
        if Clen > 0
            if isfield(layout.C, 'items') && ~isempty(layout.C.items)
                for i = 1:numel(layout.C.items)
                    for c = 1:layout.C.items(i).nCond
                        w(ptr) = inverse_variance(delta(ptr, :));
                        ptr = ptr + 1;
                        nCinfo = nCinfo + 1;
                    end
                end
            else
                rows = ptr:(ptr + Clen - 1);
                w(rows) = inverse_variance(delta(rows, :));
                nCinfo = 1;
            end
        end
    otherwise
        error('Unknown mode: %s', mode);
end
stats = struct('mode', mode, ...
    'sizes', struct('D',Dlen,'U',Ulen,'F',Flen,'C',Clen), ...
    'ninfo', struct('D',nDinfo,'F',nFinfo,'C',nCinfo,'total',nDinfo+nFinfo+nCinfo));
if mode == "pi", stats.ptrU0 = Dlen + 1; end
end

function w = inverse_variance(block)
w = 1 / max(sum(var(block, 1, 2)), eps);
end
