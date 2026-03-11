function varargout = io(action, path, varargin)
%IO Save/load PME models with a stable container struct.
%
%   pme.io("save", path, model, cfg, layout, meta)
%   S = pme.io("load", path)
%
% Saved file contains a struct S with fields:
%   - model, cfg, layout, meta, saved_at
%
% Always saves in -v7.3 for cross-language (HDF5) compatibility.

arguments
    action (1,1) string
    path (1,1) string
end
arguments (Repeating)
    varargin
end

switch lower(action)
    case "save"
        assert(numel(varargin) >= 1, 'Need at least model to save');
        S = struct();
        S.model = varargin{1};
        if numel(varargin) >= 2, S.cfg = varargin{2}; end
        if numel(varargin) >= 3, S.layout = varargin{3}; end
        if numel(varargin) >= 4, S.meta = varargin{4}; end
        S.saved_at = string(datetime("now"));
        save(path, "-struct", "S", "-v7.3");
        varargout = {};
    case "load"
        assert(isfile(path), 'Model file not found: %s', path);
        S = load(path);
        varargout = {S};
    otherwise
        error('Unknown action: %s', action);
end

end
