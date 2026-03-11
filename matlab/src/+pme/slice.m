function blocks = slice(DB, layout)
assert(size(DB,1) >= layout.totalRows, 'DB has fewer rows than layout.totalRows');

blocks = struct();
blocks.D     = DB(layout.D.rows, :);
blocks.Ubase = DB(layout.Ubase.rows, :);

if layout.F.nRows > 0
    blocks.F = DB(layout.F.rows, :);
else
    blocks.F = [];
end

if layout.C.nRows > 0
    blocks.C = DB(layout.C.rows, :);
else
    blocks.C = [];
end
end
