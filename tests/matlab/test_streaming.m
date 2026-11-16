function test_streaming()
% Replayable row readers, native-only models, and cross-Gram query encoding.
disp("Running streaming snapshot tests")
saved_rng = rng;
cleanup_rng = onCleanup(@() rng(saved_rng)); %#ok<NASGU>
rng(915)
Q = 23; S = 16; M = 3; T = 7;
lambda = [4; 1; 1; 0.1];
samples = randn(S,4); samples = samples-mean(samples,1);
[A,~] = qr(samples,0);
[Y,~] = qr(randn(Q,4),0);
w = linspace(0.4,2,Q)';
centered = (Y./sqrt(w))*diag(sqrt(S*lambda))*A';
origin = linspace(100,200,Q)';
H = centered+origin;
native = randn(M,S)+[3;7;2];
query = origin+randn(Q,T);
options = struct('eig_rtol',1e-12,'block_rows',5);
reads = 0; max_rows = 0; written = [];
model = pme.fit_streaming(@read_rows,[Q,S],@read_weights,native,options,0.8);
assert(model.nconf==3, 'The retained repeated cluster was split.');
assert(reads==ceil(Q/options.block_rows) && max_rows<=options.block_rows);
assert(norm(model.eigenvalues-lambda,inf)<1e-12);
assert(abs(model.info.total_variance-sum(lambda))<1e-12);
assert(model.info.ci_met && strcmp(model.info.solver,'snapshot'));

% Independent covariance reference compares native reconstructions, not signs.
delta = H-H(:,1); Hc = delta-mean(delta,2);
native_delta = native-native(:,1); Uc = native_delta-mean(native_delta,2);
reference = pme.direct_decompose([Hc;Uc],[w;zeros(M,1)],options);
n = model.nconf;
expected_native = mean(native,2) + reference.modes(Q+1:end,1:n)*reference.coordinates(:,1:n)';
assert(norm(pme.backmap_streaming(model,model.coordinates)-expected_native,'fro')<1e-10);
train_coordinates = pme.transform_streaming(model,@read_rows,@read_rows,S,w);
assert(norm(train_coordinates-model.coordinates,'fro')<1e-10);

% A second pass writes only bounded blocks of observation modes.
reads = 0;
with_modes = pme.fit_streaming(@read_rows,[Q,S],w,native,options,0.8,@write_modes);
assert(reads==2*ceil(Q/options.block_rows));
assert(isequal(size(written),[Q,n]));
assert(norm(written'*(w.*written)-eye(n),'fro')<1e-11);
coordinates = pme.transform_streaming(with_modes,@read_rows,@read_queries,T,@read_weights);
query_centered = (query-H(:,1))-mean(H-H(:,1),2);
expected_coordinates = query_centered'*(w.*written);
assert(norm(coordinates-expected_coordinates,'fro')<1e-10);
expected_query = mean(native,2) + reference.modes(Q+1:end,1:n)* ...
    (query_centered'*(w.*reference.modes(1:Q,1:n)))';
assert(norm(pme.backmap_streaming(with_modes,coordinates)-expected_query,'fro')<1e-10);

% Compact results remain usable without retaining a reader or the database.
temporary = [tempname,'.mat'];
cleanup_file = onCleanup(@() delete(temporary)); %#ok<NASGU>
save(temporary,'model','-v7');
saved = load(temporary);
assert(isequal(pme.backmap_streaming(saved.model,model.coordinates), ...
    pme.backmap_streaming(model,model.coordinates)));

assert_error(@() pme.fit_streaming(@(a,b) H(a:b,1:2),[Q,S],w,native,options), 'pme:StreamingBlock');
assert_error(@() pme.fit_streaming(@read_rows,[Q,S],-w,native,options), 'pme:StreamingWeights');
assert_error(@() pme.fit_streaming(@read_rows,[Q,S],w(2:end),native,options), 'pme:StreamingWeights');
assert_error(@() pme.fit_streaming(@read_rows,[Q,S],w,native(:,2:end),options), 'pme:StreamingNative');
assert_error(@() pme.fit_streaming(@read_rows,[Q,S],w,zeros(0,S),options), 'pme:StreamingNative');
assert_error(@() pme.fit_streaming(@read_rows,[Q,S],zeros(Q,1),native,options), 'pme:SnapshotRank');
assert_error(@() pme.backmap_streaming(model,zeros(T,n+1)), 'pme:StreamingCoordinates');
disp("Streaming snapshot tests passed")

    function block = read_rows(first,last)
        reads = reads+1;
        max_rows = max(max_rows,last-first+1);
        assert(last-first+1<=options.block_rows);
        block = H(first:last,:);
    end
    function block = read_queries(first,last)
        block = query(first:last,:);
    end
    function values = read_weights(first,last)
        values = w(first:last);
    end
    function write_modes(first,last,block)
        assert(last-first+1<=options.block_rows);
        if isempty(written), written = zeros(Q,size(block,2)); end
        written(first:last,:) = block;
    end
end

function assert_error(action, expected)
try
    action();
catch err
    assert(strcmp(err.identifier,expected),'Expected %s, got %s: %s',expected,err.identifier,err.message);
    return;
end
error('Expected an error, but the call succeeded.');
end
