function [DB, meta] = load_db(path, opts)
%LOAD_DB Load a data matrix from .mat (unknown variable name) or .csv/.txt.
% Returns DB as double [Nfeatures x Nsamp], and meta info.
%
% Usage:
%   [DB, meta] = load_db(path)
%   [DB, meta] = load_db(path, opts)
%
% opts fields (all optional):
%   opts.prefer        = "largest_numeric_2d"
%   opts.force_numeric = true
%   opts.transpose_if  = "auto"   % "auto"|"never"|"always"

    if nargin < 1 || isempty(path)
        error('load_db:MissingInput', 'path is required');
    end

    % Defaults
    if nargin < 2 || isempty(opts)
        opts = struct();
    end
    if ~isfield(opts,'prefer') || isempty(opts.prefer)
        opts.prefer = "largest_numeric_2d";
    end
    if ~isfield(opts,'force_numeric') || isempty(opts.force_numeric)
        opts.force_numeric = true;
    end
    if ~isfield(opts,'transpose_if') || isempty(opts.transpose_if)
        opts.transpose_if = "auto";
    end

    if isstring(path), path = char(path); end
    if ~ischar(path)
        error('load_db:BadPathType', 'path must be char or string');
    end

    [~,~,ext] = fileparts(path);
    ext = lower(ext);

    meta = struct();
    meta.source = path;

    switch ext
        case '.mat'
            S = load(path);
            names = fieldnames(S);
            if isempty(names)
                error('MAT file has no variables: %s', path);
            end

            % Collect candidate numeric 2D arrays
            cands = [];
            for i = 1:numel(names)
                v = S.(names{i});
                if isnumeric(v) && ismatrix(v) && ~isscalar(v)
                    sz = size(v);
                    cands = [cands; struct('name',names{i},'rows',sz(1),'cols',sz(2),'numel',numel(v))]; %#ok<AGROW>
                end
            end
            if isempty(cands)
                error('No numeric 2D matrix found in MAT file: %s', path);
            end

            % Pick one (default: largest by numel)
            [~,idx] = max([cands.numel]);
            chosen = cands(idx).name;

            DB = S.(chosen);
            meta.mat_varname = chosen;
            meta.candidates  = cands;

        case {'.csv', '.txt'}
            DB = readmatrix(path);
            meta.mat_varname = "";

        otherwise
            error('Unsupported extension: %s', ext);
    end

    if opts.force_numeric && ~isnumeric(DB)
        error('Loaded DB is not numeric.');
    end
    DB = double(DB);

    % Orientation: want Nfeatures x Nsamp (features=rows)
    tf = string(opts.transpose_if);
    switch tf
        case "always"
            DB = DB.';
            meta.transposed = true;
        case "auto"
            if size(DB,2) > size(DB,1)
                DB = DB.';
                meta.transposed = true;
            else
                meta.transposed = false;
            end
        case "never"
            meta.transposed = false;
        otherwise
            error('transpose_if must be auto/never/always');
    end

    meta.size = size(DB);
end
