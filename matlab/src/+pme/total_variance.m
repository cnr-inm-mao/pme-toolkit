function total = total_variance(model)
%PME.TOTAL_VARIANCE Weighted construction variance before rank truncation.
if isfield(model, 'statsW') && isfield(model.statsW, 'snapshot') && ...
        isfield(model.statsW.snapshot, 'total_variance')
    total = model.statsW.snapshot.total_variance;
else
    % Legacy models store the complete spectrum, including unresolved modes.
    total = sum(max(real(model.L_full(:)), 0));
end
if ~isscalar(total) || ~isfinite(total) || total <= 0
    error('pme:InvalidVariance', 'The model has no positive finite weighted variance.');
end
end
