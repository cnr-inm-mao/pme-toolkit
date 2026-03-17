# Input data structure

PME-toolkit operates on datasets describing the variability of parametric geometries.

## Data components

A dataset typically includes:

- geometric data
- design variables
- optional physical quantities (PI-PME / PD-PME)

---

## Geometry representation

Geometry is represented as a matrix:

    D ∈ R^(n_features × n_samples)

Where:

- n_samples = number of design realizations
- n_features = number of geometric degrees of freedom

Typical cases:

- 2D geometry → stacked coordinates
- 3D geometry → flattened mesh nodes

Example:

    [x1, x2, ..., xN
     y1, y2, ..., yN
     z1, z2, ..., zN]

---

## Design variables

Design variables are stored as:

    U ∈ R^(n_variables × n_samples)

These correspond to the original parametric model.

---

## PME embedding matrix

PME internally constructs:

    P = [D
         U]

This is the matrix used for dimensionality reduction.

---

## Optional physical data

For PI-PME / PD-PME, additional matrices may be included:

- pressure fields
- performance indicators

These are appended as additional rows in P.

---

## Key requirement

All data must be:

- aligned sample-wise
- consistent in dimension
- free of missing values (after filtering)

---

## Summary

The entire PME workflow relies on a **consistent data matrix representation**, where each column represents one design realization.
