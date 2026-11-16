# Backmapping

Backmapping reconstructs original design variables from reduced coordinates using a previously computed PME model.

---

## Overview

Backmapping maps a point in the reduced space:

    x ∈ R^N

to an approximation of the original design variables:

    u ≈ u_hat

This enables:

- interpretation of latent variables
- reconstruction of physical configurations
- integration with optimization workflows

---

## Requirements

Backmapping requires:

- a trained embedding model (from a previous PME run)
- a normalized reduced-coordinate vector in `[0,1]^N` for the standalone runner
- the original configuration file used to build the model

The case must have been run with model saving enabled. The saved format is
`model.npz` for Python and `model.mat` for MATLAB. The fitting solver is already
encoded in the model and is not selected again during backmapping.

---

## Execution

### Python

    pme-back case_back.json

### MATLAB

    run_back("case_back.json")

---

## Configuration

Backmapping is defined through a dedicated JSON file.

See:

- [Backmapping configuration](backmapping_config.md)

for the complete specification.

---

## Input

The reduced coordinates are provided through an external file (e.g. `.txt`):

- each call processes one normalized vector `x01`
- its length must equal `reduced_space.nconf`, or the full retained dimension
  when that field is omitted

---

## Output

Backmapping produces:

- reconstructed design variables
- optionally formatted outputs for downstream use

Output format and layout are defined in the configuration file.

---

## Denormalization

The standalone workflow first maps `x01` to physical reduced coordinates
`alpha`, then applies the native rows of the saved basis and restores the
original variable scaling. The analytical map is available with either fitting
solver; truncation can prevent exact recovery of a particular training design.

This depends on:

- dataset statistics
- selected denormalization rule (e.g. `"3sigma"`)

---

## Notes

- dimensionality of `x` must match the retained modes  
- values should lie within the training domain  
- extrapolation may produce non-physical or invalid configurations  
- results depend on the quality of the original embedding  

---

## Summary

Backmapping is a **post-processing step** that closes the PME workflow by linking reduced representations back to interpretable design variables.
