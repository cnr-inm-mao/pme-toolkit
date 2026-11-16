function w = read_weight_block(weights, first, last, n_rows)
%PME.READ_WEIGHT_BLOCK Read fixed metric entries for one observation block.
if isa(weights, 'function_handle')
    w = weights(first, last);
else
    if ~isnumeric(weights) || ~isvector(weights) || numel(weights) ~= n_rows
        error('pme:StreamingWeights', 'Weights must contain one value per observation row or be a block reader.');
    end
    w = weights(first:last);
end
if ~isnumeric(w) || ~isreal(w) || ~isvector(w) || numel(w) ~= last-first+1 || ...
        any(~isfinite(w(:))) || any(w(:) < 0)
    error('pme:StreamingWeights', 'Each weight block must be a finite nonnegative vector with one value per row.');
end
w = double(w(:));
end
