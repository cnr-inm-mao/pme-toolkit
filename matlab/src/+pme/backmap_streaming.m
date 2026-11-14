function native = backmap_streaming(model, coordinates)
%PME.BACKMAP_STREAMING Reconstruct supplied native coordinates from a compact model.
%   coordinates is T-by-N; native is M-by-T in the same coordinates supplied
%   to pme.fit_streaming. No clipping or variable scaling is applied here.
if ~isnumeric(coordinates) || ~isreal(coordinates) || ~ismatrix(coordinates) || ...
        size(coordinates,2) ~= model.nconf || any(~isfinite(coordinates(:)))
    error('pme:StreamingCoordinates', 'Coordinates must be a finite real T-by-N matrix.');
end
native = model.native_mean + model.native_modes * double(coordinates)';
if any(~isfinite(native(:)))
    error('pme:SnapshotOverflow', 'Native backmapping produced nonfinite values.');
end
end
