---
title: "PME-toolkit: A MATLAB/Python toolkit for design-space dimensionality reduction in parametric shape optimization"
tags:
  - MATLAB
  - Python
  - shape optimization
  - dimensionality reduction
  - parametric model embedding
  - surrogate-based design optimization
authors:
  - name: Andrea Serani
    orcid: 0000-0002-9429-1392
    affiliation: 1
  - name: Marco Diez
    affiliation: 1
affiliations:
  - name: CNR-INM, National Research Council of Italy, Institute of Marine Engineering
    index: 1
date: 11 March 2026
bibliography: paper.bib
---

# Summary

PME-toolkit is a software repository for **design-space dimensionality reduction in parametric shape optimization** based on **Parametric Model Embedding (PME)** and its physics-aware variants.

The current repository provides a **MATLAB reference implementation** for the shape-optimization workflow and a **Python scaffold** for the future port.

# Statement of need

High-dimensional parametric descriptions are common in simulation-based design optimization. They make exploration, surrogate construction, and optimization progressively more expensive as the number of design variables grows. PME-based methods address this challenge by learning reduced coordinates that retain a direct link with the original parameters, enabling interpretable reduced-space optimization together with analytical backmapping.

# Current repository scope

At this release stage:

- MATLAB is the reference implementation;
- PME, PI-PME, and PD-PME are available for the current shape-optimization scope;
- benchmark definitions are organized under `benchmarks/`;
- dataset metadata is organized under `databases/`;
- a tiny bundled test case is provided under `tests/` for self-contained validation.

# Acknowledgements

The authors acknowledge the research activities that motivated the development of PME and its physics-aware extensions.
