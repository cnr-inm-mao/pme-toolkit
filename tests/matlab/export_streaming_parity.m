function export_streaming_parity(output_file)
%EXPORT_STREAMING_PARITY Verify a shared curve and a million-row native-only fit.
tests_root = fileparts(fileparts(mfilename('fullpath')));
fixture = jsondecode(fileread(fullfile(tests_root,'data','snapshot_curve.json')));
U = fixture.native;
Uquery = fixture.query_native;
S = size(U,2);
options = fixture.options;
Q = fixture.rows;
reads = 0; max_rows = 0;
stored_modes = [];
small = pme.fit_streaming(@read_training,[Q,S],@read_weights,U,options,fixture.ci,@write_modes);
assert(small.nconf==fixture.selected_modes);
query_coordinates = pme.transform_streaming(small,@read_training,@read_queries,size(Uquery,2),@read_weights);
small_export = summarize(small);
small_export.observation_modes = stored_modes;
small_export.native_query = pme.backmap_streaming(small,query_coordinates);
small_export.query_coordinates = query_coordinates;
small_export.reader_calls = reads;
small_export.max_block_rows = max_rows;

% Same-data direct and in-memory snapshot references use the same construction mean.
H = curve_rows(1,Q,Q,U);
delta = H-H(:,1); Hc = delta-mean(delta,2);
Udelta = U-U(:,1); Uc = Udelta-mean(Udelta,2);
w = ones(Q,1)/Q;
snapshot = pme.snapshot_decompose([Hc;Uc],[w;zeros(size(U,1),1)],options);
direct = pme.direct_decompose([Hc;Uc],[w;zeros(size(U,1),1)],options);
n = small.nconf;
assert(norm(snapshot.eigenvalues-small.eigenvalues,inf)<1e-12);
assert(norm(direct.eigenvalues-small.eigenvalues,inf)<1e-12);
small_export.in_memory_native_relative_error = ...
    norm(small_export.native_training-(mean(U,2)+snapshot.modes(Q+1:end,1:n)*snapshot.coordinates(:,1:n)'),'fro')/norm(U,'fro');
small_export.direct_native_relative_error = ...
    norm(small_export.native_training-(mean(U,2)+direct.modes(Q+1:end,1:n)*direct.coordinates(:,1:n)'),'fro')/norm(U,'fro');
assert(small_export.in_memory_native_relative_error<1e-10);
assert(small_export.direct_native_relative_error<1e-10);

% Generate each observation block on demand. The complete large matrix and
% its observation modes are never constructed or stored.
Q = fixture.large_rows;
reads = 0; max_rows = 0;
large = pme.fit_streaming(@read_training,[Q,S],@read_weights,U,options,fixture.ci);
assert(large.nconf==fixture.selected_modes);
assert(reads==ceil(Q/options.block_rows));
assert(max_rows<=options.block_rows);
large_export = summarize(large);
large_export.reader_calls = reads;
large_export.max_block_rows = max_rows;
result = struct('small',small_export,'large',large_export);
fid = fopen(output_file,'w');
assert(fid>0,'Cannot open streaming parity output: %s',output_file);
cleanup_file = onCleanup(@() fclose(fid)); %#ok<NASGU>
fwrite(fid,jsonencode(result),'char');
fprintf('MATLAB streamed curve passed: Q=%d, S=%d, N=%d, max block=%d rows\n', ...
    Q,S,large.nconf,max_rows);

    function block = read_training(first,last)
        reads = reads+1;
        max_rows = max(max_rows,last-first+1);
        assert(last-first+1<=options.block_rows);
        block = curve_rows(first,last,Q,U);
    end
    function block = read_queries(first,last)
        block = curve_rows(first,last,Q,Uquery);
    end
    function wblock = read_weights(first,last)
        wblock = ones(last-first+1,1)/Q;
    end
    function write_modes(first,last,block)
        if isempty(stored_modes), stored_modes = zeros(Q,size(block,2)); end
        stored_modes(first:last,:) = block;
    end
end

function block = curve_rows(first,last,Q,U)
t = (((first:last)'-1)+0.5)/Q;
j = 1:8;
amplitudes = (0.04./(j'.^1.2)).*U;
block = 0.12*sin(pi*t) + sin(pi*t*j)*amplitudes + ...
    0.025*sin(9*pi*t)*(U(1,:).*U(2,:));
end

function out = summarize(model)
out = struct('shape',model.shape,'nconf',model.nconf, ...
    'eigenvalues',model.eigenvalues,'sample_vectors',model.sample_vectors, ...
    'native_mean',model.native_mean,'native_modes',model.native_modes, ...
    'coordinates',model.coordinates, ...
    'native_training',pme.backmap_streaming(model,model.coordinates),'info',model.info);
end
