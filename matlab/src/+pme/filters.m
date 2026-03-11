function [DBf, info, mask] = filters(DB, cfg, layout)
%PME.FILTERS Apply column-wise filters in a defined chain.
%
% Order:
%   1) remove_nan
%   2) goal-oriented (hard physical constraints)
%   3) IQR row-by-row outlier filter (legacy behaviour)
%
% Returns:
%   DBf  = DB(:,mask)
%   mask = logical(1,Nsamp) on the ORIGINAL DB columns
%   info = struct with step-by-step + cumulative counts
%
% Logging:
%   [filters][nan]  kept step / in, cumulative kept / total
%   [filters][goal] ...
%   [filters][iqr]  ...
%   [filters] total kept / total

Ns = size(DB,2);
mask = true(1,Ns);
info = struct();
info.Ns_total = Ns;

%% ---------------- Defaults ----------------
if ~isfield(cfg,'filters') || isempty(cfg.filters)
    cfg.filters = struct();
end

if ~isfield(cfg.filters,'remove_nan'), cfg.filters.remove_nan = true; end

if ~isfield(cfg.filters,'goal') || isempty(cfg.filters.goal)
    cfg.filters.goal = struct('enable',false);
end

if ~isfield(cfg.filters,'iqr') || isempty(cfg.filters.iqr)
    cfg.filters.iqr = struct('enable',false);
end
if ~isfield(cfg.filters.iqr,'k'), cfg.filters.iqr.k = 3; end
if ~isfield(cfg.filters.iqr,'start_row'), cfg.filters.iqr.start_row = "after_geom_vars"; end

% Debug switches (only prints; does not affect logic)
if ~isfield(cfg.filters,'debug'), cfg.filters.debug = struct(); end
if ~isfield(cfg.filters.debug,'goal_rows'), cfg.filters.debug.goal_rows = false; end
if ~isfield(cfg.filters.debug,'iqr_rows'),  cfg.filters.debug.iqr_rows  = false; end

% Helper for printing
print_step = @(tag, kept_step, in_step, kept_cum) ...
    fprintf('[filters][%s] kept %d / %d (cumulative %d / %d)\n', tag, kept_step, in_step, kept_cum, Ns);

% Helper: force keep baseline_col (interpreted as "baseline sample column")
function force_keep_baseline()
    if isfield(cfg,'baseline_col') && ~isempty(cfg.baseline_col)
        bc = double(cfg.baseline_col);
        if bc >= 1 && bc <= Ns
            mask(bc) = true;
        end
    end
end

%% =====================================================
%% (1) NaN filter
%% =====================================================
if cfg.filters.remove_nan
    in_step = sum(mask);
    ok = all(~isnan(DB(:,mask)), 1);   % evaluate only currently kept cols (faster & clearer)
    kept_step = sum(ok);

    % Update global mask
    idx = find(mask);
    mask(idx(~ok)) = false;

    % Never drop baseline_col
    force_keep_baseline();

    info.nan_enable   = true;
    info.nan_in       = in_step;
    info.nan_kept     = kept_step;
    info.nan_dropped  = in_step - kept_step;

    print_step('nan', kept_step, in_step, sum(mask));
else
    info.nan_enable   = false;
    info.nan_in       = sum(mask);
    info.nan_kept     = sum(mask);
    info.nan_dropped  = 0;

    % Still enforce baseline
    force_keep_baseline();

    fprintf('[filters][ nan] disabled (cumulative %d / %d)\n', sum(mask), Ns);
end

%% =====================================================
%% (2) Goal-oriented filter (physical constraints)
%% =====================================================
g = cfg.filters.goal;

if isfield(g,'enable') && g.enable

    in_step = sum(mask);

    if ~isfield(layout,'C') || layout.C.nRows == 0
        warning('[filters][goal] enabled but scalar block C is empty. Skipping goal.');
        info.goal_enable  = true;
        info.goal_skipped = true;
        info.goal_in      = in_step;
        info.goal_kept    = in_step;
        info.goal_dropped = 0;

        % Still enforce baseline
        force_keep_baseline();

        fprintf('[filters][goal] skipped (C empty), cumulative %d / %d\n', sum(mask), Ns);

    else
        info.goal_enable  = true;
        info.goal_skipped = false;

        if ~isfield(g,'baseline_col') || isempty(g.baseline_col)
            g.baseline_col = cfg.baseline_col;
        end
        baseline_col = double(g.baseline_col);

        if ~isfield(g,'metrics') || isempty(g.metrics)
            warning('[filters][goal] enabled but cfg.filters.goal.metrics is empty. Skipping goal.');
            info.goal_skipped = true;
            info.goal_in      = in_step;
            info.goal_kept    = in_step;
            info.goal_dropped = 0;

            % Still enforce baseline
            force_keep_baseline();

            fprintf('[filters][goal] skipped (metrics empty), cumulative %d / %d\n', sum(mask), Ns);

        else
            % Work on current DB slice
            idxKept = find(mask);
            DBcur = DB(:, idxKept);

            keep = true(1, size(DBcur,2));

            metrics = g.metrics;

            for i = 1:numel(metrics)

                if iscell(metrics)
                    m = metrics{i};
                else
                    m = metrics(i);
                end

                if isfield(m,'row') && ~isempty(m.row)
                    r = double(m.row);
                elseif isfield(m,'c_offset') && ~isempty(m.c_offset)
                    r = double(layout.C.rows(1) + m.c_offset - 1);
                else
                    disp(m);
                    error('[filters][goal] metric #%d must define row or c_offset.', i);
                end

                % Basic safety
                if r < 1 || r > size(DBcur,1)
                    error('[filters][goal] metric #%d resolved row r=%d out of bounds (1..%d).', i, r, size(DBcur,1));
                end
                if baseline_col < 1 || baseline_col > size(DBcur,2)
                    error('[filters][goal] baseline_col=%d out of bounds (1..%d).', baseline_col, size(DBcur,2));
                end

                base = DBcur(r, baseline_col);
                vals = DBcur(r, :);

                % --- DEBUG print: show which row is checked + 2nd column value ---
                if isfield(cfg.filters,'debug') && isfield(cfg.filters.debug,'goal_rows') && cfg.filters.debug.goal_rows
                    v2_cur = NaN;
                    if size(DBcur,2) >= 2, v2_cur = DBcur(r,2); end

                    v2_orig = NaN;
                    if size(DB,2) >= 2, v2_orig = DB(r,2); end

                    fprintf('[filters][goal][debug] metric %d: rule=%s, r=%d, baseline_col=%d, base=%.6g, DBcur(r,2)=%.6g, DB(r,2)=%.6g\n', ...
                        i, string(m.rule), r, baseline_col, base, v2_cur, v2_orig);
                end

                switch lower(string(m.rule))
                    case "leq_baseline"
                        fac = 1;
                        if isfield(m,'factor') && ~isempty(m.factor), fac = m.factor; end
                        keep = keep & (vals <= fac*base);

                    case "geq_baseline"
                        fac = 1;
                        if isfield(m,'factor') && ~isempty(m.factor), fac = m.factor; end
                        keep = keep & (vals >= fac*base);

                    case "between_baseline"
                        if ~isfield(m,'min') || isempty(m.min) || ~isfield(m,'max') || isempty(m.max)
                            error('[filters][goal] between_baseline requires keys "min" and "max".');
                        end
                        keep = keep & (vals >= m.min*base) & (vals <= m.max*base);

                    case "positive"
                        keep = keep & (vals > 0);

                    case "nonnegative"
                        keep = keep & (vals >= 0);

                    otherwise
                        error('[filters][goal] unknown goal rule: %s', string(m.rule));
                end
            end

            kept_step = sum(keep);

            % Update global mask: drop those not kept
            drop_local = ~keep;
            mask(idxKept(drop_local)) = false;

            % Never drop baseline_col
            force_keep_baseline();

            info.goal_in      = in_step;
            info.goal_kept    = kept_step;
            info.goal_dropped = in_step - kept_step;

            print_step('goal', kept_step, in_step, sum(mask));
        end
    end

else
    info.goal_enable  = false;
    info.goal_skipped = false;
    info.goal_in      = sum(mask);
    info.goal_kept    = sum(mask);
    info.goal_dropped = 0;

    % Still enforce baseline
    force_keep_baseline();

    fprintf('[filters][goal] disabled (cumulative %d / %d)\n', sum(mask), Ns);
end

%% =====================================================
%% (3) IQR row-by-row outlier filter (legacy)
%% =====================================================
iq = cfg.filters.iqr;

if isfield(iq,'enable') && iq.enable

    in_step = sum(mask);

    % Decide start row r0
    if ischar(iq.start_row) || isstring(iq.start_row)

        switch lower(string(iq.start_row))

            case "after_geom_vars"
                % legacy: idx = K*Jdir + Mbase
                K = sum([cfg.geom.patches.K]);  % multipatch supported (sum)
                idx = K * cfg.geom.Jdir + cfg.vars.Mbase;
                r0 = idx + 1;

            case "after_layout_ubase"
                % after D + Ubase (Mbase)
                r0 = layout.D.nRows + cfg.vars.Mbase + 1;

            case "after_c_block_start"
                % start IQR only on scalars C
                if ~isfield(layout,'C') || layout.C.nRows==0
                    warning('[filters][ iqr] start_row=after_c_block_start but C empty. Skipping IQR.');
                    r0 = [];
                else
                    r0 = layout.C.rows(1);
                end

            otherwise
                error('[filters][ iqr] unknown start_row keyword: %s', string(iq.start_row));
        end

    else
        r0 = double(iq.start_row);
    end

    if isempty(r0)
        info.iqr_enable   = true;
        info.iqr_skipped  = true;
        info.iqr_in       = in_step;
        info.iqr_kept     = in_step;
        info.iqr_dropped  = 0;

        % Still enforce baseline
        force_keep_baseline();

        fprintf('[filters][ iqr] skipped (no valid start row), cumulative %d / %d\n', sum(mask), Ns);

    else
        info.iqr_enable   = true;
        info.iqr_skipped  = false;

        % Work on current DB slice
        idxKept = find(mask);
        DBcur = DB(:, idxKept);

        r0 = max(1, min(r0, size(DBcur,1)));
        k = iq.k;

        % --- DEBUG print: show IQR row range actually used ---
        if isfield(cfg.filters,'debug') && isfield(cfg.filters.debug,'iqr_rows') && cfg.filters.debug.iqr_rows
            fprintf('[filters][ iqr][debug] applying IQR from r0=%d to rEnd=%d (k=%g)\n', r0, size(DBcur,1), k);
        end

        valid_cols = true(1, size(DBcur,2));

        for r = r0:size(DBcur,1)
            row_data = DBcur(r,:);

            Q1 = prctile(row_data,25);
            Q3 = prctile(row_data,75);
            IQR = Q3 - Q1;

            lowerBound = Q1 - k*IQR;
            upperBound = Q3 + k*IQR;

            valid_cols = valid_cols & (row_data >= lowerBound) & (row_data <= upperBound);
        end

        kept_step = sum(valid_cols);

        % Update global mask
        mask(idxKept(~valid_cols)) = false;

        % Never drop baseline_col
        force_keep_baseline();

        info.iqr_in            = in_step;
        info.iqr_kept          = kept_step;
        info.iqr_dropped       = in_step - kept_step;
        info.iqr_k             = k;
        info.iqr_start_row_abs = r0;

        print_step('iqr', kept_step, in_step, sum(mask));
    end

else
    info.iqr_enable   = false;
    info.iqr_skipped  = false;
    info.iqr_in       = sum(mask);
    info.iqr_kept     = sum(mask);
    info.iqr_dropped  = 0;

    % Still enforce baseline
    force_keep_baseline();

    fprintf('[filters][ iqr] disabled (cumulative %d / %d)\n', sum(mask), Ns);
end

%% ---------------- Final baseline check ----------------
if isfield(cfg,'baseline_col') && ~isempty(cfg.baseline_col)
    bc = double(cfg.baseline_col);
    if bc >= 1 && bc <= Ns
        if ~mask(bc)
            error('[filters] baseline_col=%d was dropped (this must never happen).', bc);
        end
    end
end

%% =====================================================
% Final
DBf = DB(:, mask);

info.total_kept    = sum(mask);
info.total_dropped = Ns - info.total_kept;

fprintf('[filters] total kept %d / %d samples\n', info.total_kept, Ns);
fprintf('');

end
