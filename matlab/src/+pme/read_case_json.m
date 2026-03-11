function cfg = read_case_json(jsonFile)
%PME.READ_CASE_JSON Load a PME case config from JSON and resolve relative paths.
%
% JSON is the canonical input format (uses jsondecode).
% All file paths inside cfg.io / cfg.vars that are relative are resolved
% with respect to the folder containing jsonFile.
%
% Conventions:
% - Indices in JSON are 0-based (Python-friendly). MATLAB converts to 1-based:
%   * cfg.baseline_col
%   * cfg.filters.goal.metrics(:).c_offset
%
% Supported optional fields:
% - cfg.vars.Urange_file : path to a file containing Urange (numeric Mx2 [min max])
%       Supported extensions: .mat .csv .txt .dat
%       For .mat: variable name "Urange" preferred, otherwise single variable in MAT.
% - cfg.io.dbfile        : path to database (.mat/.csv/.txt etc.)
% - cfg.io.matvar        : variable name inside .mat (optional; loader may auto-detect)

arguments
    jsonFile (1,1) string
end

assert(isfile(jsonFile), 'Case JSON not found: %s', jsonFile);
baseDir = fileparts(jsonFile);

cfg = jsondecode(fileread(jsonFile));
cfg = normalize_strings(cfg);

% ----------------------------
% io defaults + resolve paths
% ----------------------------
if ~isfield(cfg,'io') || isempty(cfg.io), cfg.io = struct(); end

if isfield(cfg.io,'dbfile') && ~isempty(cfg.io.dbfile)
    cfg.io.dbfile = resolve_path(baseDir, cfg.io.dbfile);
end

if ~isfield(cfg.io,'transpose_if') || isempty(cfg.io.transpose_if), cfg.io.transpose_if = "auto"; end
if ~isfield(cfg.io,'outdir')       || isempty(cfg.io.outdir),       cfg.io.outdir = "results"; end
if ~isfield(cfg.io,'save_model')   || isempty(cfg.io.save_model),   cfg.io.save_model = true; end

% ----------------------------
% vars defaults + Urange load
% ----------------------------
if ~isfield(cfg,'vars') || isempty(cfg.vars), cfg.vars = struct(); end
if ~isfield(cfg.vars,'idx_active'), cfg.vars.idx_active = []; end

if isfield(cfg.vars,'Urange_file') && ~isempty(cfg.vars.Urange_file)
    urFile = resolve_path(baseDir, cfg.vars.Urange_file);
    assert(isfile(urFile), 'Urange_file not found: %s', urFile);

    Ur = load_urange_any(urFile);

    if ~isnumeric(Ur) || size(Ur,2) ~= 2
        error('Urange must be numeric Mx2 [min max]. Got size %s from file %s.', mat2str(size(Ur)), urFile);
    end

    cfg.vars.Urange = Ur;
    cfg.vars.Urange_file = string(urFile); % store resolved path for provenance
end

% ---- indices: JSON 0-based -> MATLAB 1-based
if isfield(cfg,'baseline_col') && ~isempty(cfg.baseline_col)
    cfg.baseline_col = cfg.baseline_col + 1;
end

% idx_active: JSON 0-based -> MATLAB 1-based
if isfield(cfg,'vars') && isfield(cfg.vars,'idx_active') && ~isempty(cfg.vars.idx_active)
    cfg.vars.idx_active = cfg.vars.idx_active + 1;
end

% goal metric indices: JSON 0-based -> MATLAB 1-based
if isfield(cfg,'filters') && isfield(cfg.filters,'goal') && isfield(cfg.filters.goal,'metrics')

    m = cfg.filters.goal.metrics;

    if ~isempty(m)
        for i = 1:numel(m)

            % Get i-th metric (supports cell or struct array)
            if iscell(m)
                mi = m{i};
            else
                mi = m(i);
            end

            % Convert indices if present
            if isstruct(mi)
                if isfield(mi,'c_offset') && ~isempty(mi.c_offset)
                    mi.c_offset = mi.c_offset + 1;
                end
                if isfield(mi,'row') && ~isempty(mi.row)
                    mi.row = mi.row + 1;
                end
            end

            % Write back
            if iscell(m)
                m{i} = mi;
            else
                m(i) = mi;
            end
        end
    end

    cfg.filters.goal.metrics = m;
end

end

% ======================================================================

function Ur = load_urange_any(urFile)
% Load Urange from .mat or from text-like formats (csv/txt/dat).
urFile = string(urFile);
[~,~,ext] = fileparts(urFile);
ext = lower(ext);

switch ext
    case ".mat"
        S = load(urFile);

        if isfield(S,'Urange')
            Ur = S.Urange;
        else
            f = fieldnames(S);
            if numel(f) == 1
                Ur = S.(f{1});
            else
                error(['Urange_file MAT contains multiple variables and none is named "Urange". ' ...
                       'Please store a single variable or name it Urange. File: %s'], urFile);
            end
        end

        if isstruct(Ur)
            error('Loaded Urange is a struct; expected numeric matrix. File: %s', urFile);
        end

    case {".csv",".txt",".dat"}
        % readmatrix handles commas/spaces/tabs reasonably well
        Ur = readmatrix(urFile);

    otherwise
        error('Unsupported Urange_file extension: %s (file: %s).', ext, urFile);
end

end

function p = resolve_path(baseDir, pIn)
% Resolve pIn relative to baseDir unless it's an absolute path.
% Does NOT require the path to exist at resolution time.
pIn = string(pIn);
if strlength(pIn)==0
    p = "";
    return;
end

if isAbsolutePath(pIn)
    p = pIn;
else
    p = string(fullfile(baseDir, pIn));
end
end

function tf = isAbsolutePath(p)
p = string(p);
if strlength(p)==0, tf = false; return; end
% unix absolute
if startsWith(p, "/"), tf = true; return; end
% windows absolute (C:\ or C:/)
tf = ~isempty(regexp(char(p), '^[A-Za-z]:[\\/]', 'once'));
end

function x = normalize_strings(x)
% Recursively convert char to string inside structs/cells.
% Leaves numeric/logical untouched.
if isstruct(x)
    fn = fieldnames(x);
    for i = 1:numel(x)                 % handle struct arrays too
        for k = 1:numel(fn)
            x(i).(fn{k}) = normalize_strings(x(i).(fn{k}));
        end
    end
elseif iscell(x)
    for i = 1:numel(x)
        x{i} = normalize_strings(x{i});
    end
elseif ischar(x)
    x = string(x);
else
    % numeric/logical/string/etc -> leave as is
end

end
