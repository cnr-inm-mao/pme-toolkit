---
title: "PME-toolkit: a reproducible framework for design-space dimensionality reduction in parametric shape optimization"
tags:
  - dimensionality reduction
  - shape optimization
  - surrogate modeling
  - design optimization
authors:
  - name: Andrea Serani
    affiliation: 1
affiliations:
  - name: CNR-INM, National Research Council-Institute of Marine Engineering, Rome, Italy
    index: 1
date: 2026
bibliography: paper.bib
---

# Summary

PME-toolkit is an open-source framework for design-space dimensionality reduction in parametric shape optimization based on Parametric Model Embedding (PME) @Serani2023PME and its physics-aware extensions (PI-PME, PD-PME) @Serani2025EWC.

The software builds upon previous developments and applications of PME in aerodynamic and hydrodynamic shape optimization @SeraniAST, @Serani2024JMSE, @Gaggero2026AOR, as well as related dimensionality-reduction studies.

The software provides a reproducible, benchmark-driven workflow with dual Python and MATLAB implementations, enabling consistent analysis, cross-validation, and integration within simulation-based design optimization pipelines.

# Statement of need

Simulation-Based Design Optimization (SBDO) is often limited by the curse of dimensionality @Bellman1957, which arises in high-dimensional parametric design spaces.

PME-toolkit addresses this limitation by constructing a low-dimensional embedding of the design space that preserves a direct mapping to the original variables, enabling analytical backmapping and efficient optimization in reduced coordinates.

Existing dimensionality-reduction approaches in shape optimization @Serani2025Survey typically lack:

* a direct link to the original design variables,
* reproducibility across implementations,
* or integration within engineering workflows.

PME-toolkit fills this gap by providing:

* a unified implementation of PME, PI-PME, and PD-PME,
* a JSON-driven workflow for reproducibility,
* cross-language validation between Python and MATLAB,
* benchmark-ready configurations for representative shape optimization problems.

PME-toolkit establishes a reproducible and extensible foundation for integrating design-space dimensionality reduction methods within modern SBDO pipelines.

# Key features

* Dual Python/MATLAB implementation with cross-language validation
* Implementation of PME, PI-PME, and PD-PME
* Analytical backmapping to original parametric variables
* JSON-based reproducible workflows
* Benchmark configurations for glider and airfoil cases
* Cross-language regression testing

# Availability

* Source code: https://github.com/cnr-inm-mao/pme-toolkit
* Documentation: https://cnr-inm-mao.github.io/pme-toolkit/
* PyPI package: https://pypi.org/project/pme-toolkit/
* DOI: https://doi.org/10.5281/zenodo.18962859

# Acknowledgements

The author acknowledges the support of the Italian Ministry of University and Research (MUR) through the PRIN 2022 program, project BIODRONES (20227JNM52, CUP B53D230055600), and the National Recovery and Resilience Plan (PNRR), Sustainable Mobility Center (CNMS), Spoke 3 Waterways (CN00000023, CUP B43C22000440001).

This work was also conducted within the NATO AVT-404 Research Task Group on “Enhanced Design Processes of Military Vehicles through Machine Learning Methods.”
