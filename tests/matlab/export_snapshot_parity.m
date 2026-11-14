function export_snapshot_parity(output_path)
%EXPORT_SNAPSHOT_PARITY Export live MATLAB results for Python comparison.
tests_root = fileparts(fileparts(mfilename('fullpath')));
if nargin < 1
    output_path = fullfile(tests_root, 'reference', 'snapshot_matlab_parity.json');
end
fixture = jsondecode(fileread(fullfile(tests_root, 'data', 'snapshot_parity.json')));
result = struct();
for mode = ["pme", "pi", "pd"]
    cfg = fixture.cfg;
    cfg.mode = mode;
    model = pme.fit(fixture.db, cfg);
    n = model.sizes.nconf;
    scores = model.ak_full(:,1:n);
    A = scores ./ sqrt(size(fixture.db,2)*model.Lr');
    if mode == "pd"
        native_rows = 1:model.Uinfo.Mact;
    else
        native_rows = model.layout.D.nRows+(1:model.Uinfo.Mact);
    end
    result.(char(mode)) = struct('eigenvalues',model.Lr, ...
        'nconf',n,'weights',model.W, ...
        'native_reconstruction',model.Zr(native_rows,:)*scores', ...
        'sample_projector',A*A', ...
        'total_variance',model.statsW.snapshot.total_variance, ...
        'achieved_ci',model.statsW.snapshot.achieved_ci);
end
parent = fileparts(output_path);
if ~isempty(parent) && ~isfolder(parent), mkdir(parent); end
fid = fopen(output_path,'w');
assert(fid~=-1,'Could not create parity output: %s',output_path);
cleanup = onCleanup(@() fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(result));
end
