function ensure_case_inputs(jsonFile)
%PME.ENSURE_CASE_INPUTS Ensure dataset files required by a case exist.
%
% Dataset location inferred from dbfile / Urange_file in case.json.

arguments
    jsonFile (1,1) string
end

jsonFile = string(jsonFile);

% resolve case path relative to current working directory
if ~is_absolute_path(jsonFile)
    jsonAbs = string(fullfile(pwd, jsonFile));
else
    jsonAbs = jsonFile;
end

assert(isfile(jsonAbs), 'Case JSON not found: %s', jsonAbs);

caseDir = string(fileparts(jsonAbs));

raw = jsondecode(fileread(jsonAbs));

dbfile = "";
urangeFile = "";

if isfield(raw,'io') && isfield(raw.io,'dbfile') && ~isempty(raw.io.dbfile)
    dbfile = normalize_target(fullfile(caseDir, string(raw.io.dbfile)));
end

if isfield(raw,'vars') && isfield(raw.vars,'Urange_file') && ~isempty(raw.vars.Urange_file)
    urangeFile = normalize_target(fullfile(caseDir, string(raw.vars.Urange_file)));
end

missing = strings(0);

if strlength(dbfile) > 0 && ~isfile(dbfile)
    missing(end+1) = "dbfile";
end

if strlength(urangeFile) > 0 && ~isfile(urangeFile)
    missing(end+1) = "Urange_file";
end

if isempty(missing)
    fprintf('[dataset] all required inputs already available.\n');
    return;
end

fprintf('[dataset] missing inputs detected: %s\n', strjoin(missing,", "));

% infer dataset directory
if strlength(dbfile) > 0
    datasetDir = string(fileparts(dbfile));
elseif strlength(urangeFile) > 0
    datasetDir = string(fileparts(urangeFile));
else
    error('Could not infer dataset directory from case.json.');
end

metaFile = fullfile(datasetDir,"dataset.json");

assert(isfile(metaFile), ...
    'Missing dataset.json in shared dataset directory: %s', datasetDir);

meta = jsondecode(fileread(metaFile));

archiveUrl  = string(meta.download.archive_url);
archiveName = string(meta.download.archive_name);
archivePath = fullfile(datasetDir, archiveName);

fprintf('[dataset] shared dataset directory: %s\n', datasetDir);
fprintf('[dataset] archive url: %s\n', archiveUrl);

if ~isfolder(datasetDir)
    mkdir(datasetDir);
end

% --------------------------------------------------------
% DOWNLOAD
% --------------------------------------------------------
if ~isfile(archivePath)

    fprintf('[dataset] downloading archive...\n');

    try
        download_with_progress(archiveUrl, archivePath);
    catch
        fprintf('[dataset] fallback download (no progress)...\n');
        websave(archivePath, archiveUrl);
    end

else
    fprintf('[dataset] archive already present locally: %s\n', archivePath);
end

% --------------------------------------------------------
% UNZIP
% --------------------------------------------------------
fprintf('[dataset] extracting archive...\n');

files = unzip(archivePath, datasetDir);

fprintf('[dataset] extracted %d files\n', numel(files));

% --------------------------------------------------------
% FLATTEN (handle base folder in zip)
% --------------------------------------------------------
d = dir(datasetDir);
d = d([d.isdir] & ~startsWith({d.name}, '.'));

for k = 1:numel(d)

    sub = fullfile(datasetDir, d(k).name);

    files = dir(fullfile(sub, '*.mat'));

    for i = 1:numel(files)

        src = fullfile(files(i).folder, files(i).name);
        dst = fullfile(datasetDir, files(i).name);

        fprintf('[dataset] moving %s -> %s\n', src, dst);

        movefile(src, dst, 'f');

    end
end

% --------------------------------------------------------
% FINAL CHECK
% --------------------------------------------------------
if strlength(dbfile) > 0 && ~isfile(dbfile)
    error('Dataset download/unzip completed, but dbfile missing: %s', dbfile);
end

if strlength(urangeFile) > 0 && ~isfile(urangeFile)
    error('Dataset download/unzip completed, but Urange_file missing: %s', urangeFile);
end

fprintf('[dataset] dataset ready.\n');

end


% ============================================================
% UTILITIES
% ============================================================

function tf = is_absolute_path(p)

p = char(p);

tf = startsWith(p, filesep) || ...
     ~isempty(regexp(p,'^[A-Za-z]:[\\/]', 'once'));

end


function p = normalize_target(pIn)

% normalize ../ ./ segments

f = java.io.File(char(pIn));

parent = f.getParentFile();

name = string(char(f.getName()));

p = string(char(parent.getCanonicalPath()));

p = string(fullfile(p,name));

end


function download_with_progress(url,outfile)

import matlab.net.*
import matlab.net.http.*

uri = URI(url);

req = RequestMessage;

resp = req.send(uri);

lenField = resp.getFields('Content-Length');

if isempty(lenField)

    websave(outfile,url);

    return

end

total = str2double(lenField.Value);

fprintf('[dataset] size %.1f MB\n', total/1024/1024);

fid = fopen(outfile,'w');

data = resp.Body.Data;

bytes = 0;

chunk = 8192;

while true

    buf = data.read(chunk);

    if isempty(buf)
        break
    end

    fwrite(fid,buf,'uint8');

    bytes = bytes + numel(buf);

    fprintf('\r[dataset] downloaded %.1f %%',100*bytes/total);

end

fprintf('\n');

fclose(fid);

end
