function w = weight_diagonal(W)
%PME.WEIGHT_DIAGONAL Read current vector or legacy dense diagonal weights.
if ~isnumeric(W) || ~isreal(W)
    error('pme:InvalidWeights', 'Weights must be a real numeric vector or diagonal matrix.');
end
if isvector(W)
    w = W(:);
elseif ismatrix(W) && size(W, 1) == size(W, 2)
    w = diag(W);
    if nnz(W) ~= nnz(w)
        error('pme:InvalidWeights', 'Legacy weight matrices must be diagonal.');
    end
else
    error('pme:InvalidWeights', 'Weights must be a vector or a square diagonal matrix.');
end
if any(~isfinite(w)) || any(w < 0)
    error('pme:InvalidWeights', 'Weights must be finite and nonnegative.');
end
end
