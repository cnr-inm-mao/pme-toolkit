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
- a reduced coordinates vector
- the original configuration file used to build the model

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

- Backmapping configuration

for the complete specification.

---

## Input

The reduced coordinates are provided through an external file (e.g. `.txt`):

- each configuration corresponds to one vector `x`
- dimensionality must match the number of retained modes

---

## Output

Backmapping produces:

- reconstructed design variables
- optionally formatted outputs for downstream use

Output format and layout are defined in the configuration file.

---

## Denormalization

Backmapping includes a denormalization step that maps reduced coordinates back to the original variable scale.

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
