function block = read_observation_block(reader, first, last, n_samples)
%PME.READ_OBSERVATION_BLOCK Read and validate one raw observation block.
if ~isa(reader, 'function_handle')
    error('pme:StreamingReader', 'The observation reader must be a function handle.');
end
block = reader(first, last);
if ~isnumeric(block) || ~isreal(block) || ~ismatrix(block) || ...
        ~isequal(size(block), [last-first+1, n_samples]) || any(~isfinite(block(:)))
    error('pme:StreamingBlock', ...
        'Observation reader must return a finite real %d-by-%d block.', last-first+1, n_samples);
end
block = double(block);
end
