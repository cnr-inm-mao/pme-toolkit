function nconf = choose_nconf(L, CI)
cum = cumsum(L);
tot = cum(end);
if tot <= 0
    nconf = 1;
    return;
end
ratio = cum / tot;
nconf = find(ratio >= CI, 1, 'first');
if isempty(nconf), nconf = numel(L); end
end
