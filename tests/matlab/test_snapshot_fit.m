function test_snapshot_fit()
% Same database and JSON configuration are consumed by the Python tests.
disp("Running snapshot workflow tests")
tests_root = fileparts(fileparts(mfilename('fullpath')));
fixture = jsondecode(fileread(fullfile(tests_root, 'data', 'snapshot_parity.json')));
DB = fixture.db;
temporary = tempname;
mkdir(temporary);
cleanup = onCleanup(@() rmdir(temporary, 's')); %#ok<NASGU>

for mode = ["pme", "pi", "pd"]
    cfg = fixture.cfg;
    cfg.mode = mode;
    model = pme.fit(DB, cfg);
    assert(strcmp(model.version, '1.3.0'));
    assert(iscolumn(model.W));
    assert(all(model.L_full > model.statsW.snapshot.eigenvalue_threshold));
    assert(size(model.Z_full,2) == model.statsW.snapshot.numerical_rank);
    assert(norm(model.Z_full'*(model.W.*model.Z_full)-eye(numel(model.L_full)),'fro') < 1e-8);

    blocks = pme.slice(DB, model.layout);
    [Uact, Uinfo] = pme.prepare_vars(blocks.Ubase, model.cfg, blocks, struct('verbose',false));
    P = pme.compose_P(blocks.D, Uact, blocks.F, blocks.C, model.cfg);
    Pc = P-model.P0-model.delta_m;
    weights_expected = zeros(size(model.W));
    if mode == "pd"
        native_rows = 1:3;
        field_start = 4;
    else
        native_rows = 7:9;
        weights_expected(1:6) = 1/sum(var(blocks.D,1,2));
        field_start = 10;
    end
    if mode ~= "pme"
        for c = 1:2
            rows = field_start+(c-1)*2+(0:1);
            weights_expected(rows) = 1/max(sum(var(Pc(rows,:),1,2)),eps);
        end
        scalar_start = field_start+4;
        weights_expected(scalar_start) = 1/max(var(Pc(scalar_start,:),1,2),eps);
        weights_expected(scalar_start+1) = 1/eps;
    end
    assert(norm(model.W-weights_expected,inf) < 1e-10);
    assert(all(model.W(native_rows)==0));
    [dense_weights, ~] = pme.weights(P-model.P0, model.layout, model.cfg, Uinfo, blocks);
    assert(isequal(diag(dense_weights),model.W));

    transformed = pme.transform(model,DB);
    scores = model.ak_full(:,1:model.sizes.nconf);
    assert(norm(transformed-scores,'fro') < 1e-9);
    legacy_model = model;
    legacy_model.W = diag(model.W);
    saved_file = fullfile(temporary, mode+".mat");
    save(saved_file, 'legacy_model', '-v7');
    saved = load(saved_file);
    assert(norm(pme.transform(saved.legacy_model,DB)-scores,'fro') < 1e-9);

    % Compare spectra and native reconstructions with an independent direct solve.
    active = model.W > 0;
    B = sqrt(model.W(active)) .* Pc(active,:);
    [Y, lambda] = eig((B*B')/size(DB,2),'vector');
    [lambda, order] = sort(lambda,'descend');
    n = model.sizes.nconf;
    direct_Z = Y(:,order(1:n)) ./ sqrt(model.W(active));
    direct_X = Pc(active,:)'*(model.W(active).*direct_Z);
    direct_U = (Pc(native_rows,:)*direct_X) ./ (size(DB,2)*lambda(1:n)');
    snapshot_native = model.Zr(native_rows,:)*scores';
    assert(norm(lambda(1:n)-model.Lr,inf)<1e-10);
    assert(norm(snapshot_native-direct_U*direct_X','fro')<1e-8);
    total_variance = sum(B(:).^2)/size(DB,2);
    assert(abs(model.statsW.snapshot.achieved_ci-sum(model.Lr)/total_variance)<1e-10);

    if mode == "pi"
        assert(abs(model.statsW.snapshot.total_variance-4)<1e-12);
        assert(model.statsW.ninfo.total==5);
        rep = pme.report(model,DB,fullfile(temporary,'report'));
        assert(norm(rep.nmse.ev_global-rep.nmse.retained_variance,inf)<1e-9);
        assert(all(rep.nmse.var_t(end,:)==0));
        assert(rep.kmax>=model.sizes.nconf);
    end
end
disp("Snapshot workflow tests passed")
end
