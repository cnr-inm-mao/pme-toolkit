function [W, stats] = weights(delta, layout, cfg, Uinfo, blocks)
%PME.WEIGHTS Compatibility interface returning the dense diagonal metric.
% Fitting uses pme.weights_diag directly to avoid the quadratic allocation.
[w, stats] = pme.weights_diag(delta, layout, cfg, Uinfo, blocks);
W = diag(w);
end
