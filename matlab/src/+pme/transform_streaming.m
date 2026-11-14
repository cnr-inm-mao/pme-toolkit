function coordinates = transform_streaming(model, training_reader, query_reader, query_samples, weights)
%PME.TRANSFORM_STREAMING Encode new observations with blockwise cross-Gram products.
%   Readers return the same observation rows with their own sample columns.
%   The training reader and fixed weights must match those used during fit.
%   Query rows are centered with the construction means, never query means.
%   Output coordinates has query_samples rows and model.nconf columns.

validateattributes(query_samples, {'numeric'}, {'scalar','integer','positive','finite'});
Q = model.shape(1); S = model.shape(2);
block_rows = model.info.block_rows;
cross_gram = zeros(query_samples, S);
for first = 1:block_rows:Q
    last = min(first + block_rows - 1, Q);
    construction = pme.read_observation_block(training_reader, first, last, S);
    queries = pme.read_observation_block(query_reader, first, last, query_samples);
    delta = construction - construction(:,1);
    delta_mean = mean(delta,2);
    centered = delta - delta_mean;
    centered_queries = (queries - construction(:,1)) - delta_mean;
    w = pme.read_weight_block(weights, first, last, Q);
    scaled = sqrt(w) .* (centered / sqrt(S));
    scaled_queries = sqrt(w) .* (centered_queries / sqrt(S));
    cross_gram = cross_gram + scaled_queries' * scaled;
end
scales = sqrt(S) ./ sqrt(model.eigenvalues(1:model.nconf)');
coordinates = cross_gram * (model.sample_vectors .* scales);
if any(~isfinite(coordinates(:)))
    error('pme:SnapshotOverflow', 'Cross-Gram projection produced nonfinite coordinates.');
end
end
