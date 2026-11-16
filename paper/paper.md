---
title: "PME-toolkit: parametric model embedding for design-space dimensionality reduction in Python and MATLAB"
tags:
  - dimensionality reduction
  - shape optimization
  - surrogate modeling
  - design optimization
authors:
  - name: Andrea Serani
    orcid: 0000-0002-8814-1793
    affiliation: 1
affiliations:
  - name: CNR-INM, National Research Council-Institute of Marine Engineering, Rome, Italy
    index: 1
date: 16 November 2026
bibliography: paper.bib
---

# Summary

Shape optimization varies geometry parameters and evaluates each candidate through numerical simulations. Exploring many parameters can require a large computational budget. PME-toolkit builds a smaller set of design coordinates from sampled shapes and, when available, simulation outputs. An analytical backmap converts a reduced design into the original parameters, so that new candidates can be passed to the same geometry generator. In the [RAE2822 airfoil benchmark](https://cnr-inm-mao.github.io/pme-toolkit/zenodo-regression/), five reduced coordinates describe a 20-parameter shape family while retaining more than 95% of the sampled geometric variance.

The toolkit implements Parametric Model Embedding (PME) [@Serani2023PME], Physics-Informed PME (PI-PME), and Physics-Driven PME (PD-PME) [@Serani2025EWC]. These formulations use geometric observations, combined geometric and physical observations, or physical observations alone, respectively. Python and MATLAB implementations share case definitions, numerical conventions, reporting, and verification protocols. Version 1.3.0 provides direct and snapshot eigensolvers, together with a separate interface for observations read in blocks [@Serani2026Toolkit].

# Statement of need

Simulation-based design optimization combines expensive numerical models with parameterizations that may contain redundant or weakly influential directions. Dimensionality reduction can make the search more manageable. Its usefulness depends on which variations are retained and how reduced designs are converted into inputs for the simulation workflow [@Serani2025Survey]. Geometric variance alone may also be insufficient when performance depends on features represented more clearly by physical fields or scalar responses.

PME-toolkit pairs observation data with the design parameters used to generate each sample. It assigns weights to the observation sources and computes an affine backmap to the native parameters. Researchers can use the resulting models in their geometry-generation and simulation workflows. Preprocessing, weighting, dimensionality selection, projection, backmapping, and diagnostic plots follow a common sequence for all three PME formulations. The published formulations and their aerodynamic, hydrodynamic, and propeller applications provide the scientific basis for these operations [@SeraniAST; @Serani2024JMSE; @Gaggero2026AOR].

# State of the field

General-purpose libraries such as scikit-learn provide principal-component analysis and inverse transformations in the fitted feature space [@Pedregosa2011]. Geometry-oriented tools such as PyGeM provide parameterized deformation methods that can supply shape observations [@Tezzele2021PyGeM]. PME-toolkit connects these two tasks: it constructs a reduced space from geometric or physical observations and maps its coordinates to the parameters of the supplied geometry model. The native parameters remain in the backmap even though they have zero weight in the reduction metric.

The MATLAB and Python implementations read the same JSON case definitions and use matching weighting conventions, projection operations, and native-parameter backmaps. Keeping these operations together lets researchers switch between PME, PI-PME, and PD-PME using the same data preparation and output tools. Shared benchmarks check numerical agreement between the two languages. Geometry and simulation packages supply their observations through array-based interfaces.

# Software design

The case workflow separates data loading and filtering, preparation of active design variables, construction of observation weights, decomposition, and downstream analysis. JSON configurations specify data sources, variable bounds, physical quantities, filters, and the requested retained-variance fraction. PME, PI-PME, and PD-PME share these operations. Both implementations reject physics-aware configurations without physical inputs, preventing a requested PI-PME or PD-PME analysis from silently omitting its physical information. Small fixtures support installation checks, while larger engineering databases are retrieved from separately archived datasets.

Direct and snapshot decomposition operate on the same centered samples and diagonal metric. The direct solver uses a symmetric covariance matrix restricted to positive-weight observation rows; the snapshot solver uses a sample Gram matrix and recovers the modes from its eigenvectors. Automatic selection chooses the smaller eigenproblem. These alternatives share numerical-rank thresholds, retained-variance accounting, and the model interface used for projection, backmapping, reporting, and plotting. Diagonal weights are stored as vectors, avoiding a dense metric matrix. Native parameters have zero metric weight but remain in the recovered modes, preserving the analytical backmap.

This design addresses two distinct memory regimes. The standard case workflow holds its input database in memory. For larger observation dimensions, the streaming interface accepts repeatable row-block readers and accumulates the snapshot matrix without retaining the full observation array. A compact model stores the factors required for native backmapping; observation modes can optionally be written in a second pass. Projection of new observations uses construction means and consistent global weights; physics-aware projection requires the corresponding physical observations for each query. The sample Gram matrix remains dense, so its memory cost still grows quadratically with the number of construction samples.

Mode selection uses the complete weighted trace and retains an entire repeated-eigenvalue cluster when the cluster intersects the requested variance threshold. Numerically unresolved modes are excluded and reported. Retained observation variance does not guarantee exact recovery of all native-parameter variations, satisfaction of parameter bounds, or physical feasibility. These quantities require separate assessment in the consuming design workflow.

# Research impact statement

PME-toolkit provides executable engineering cases and numerical verification materials for research on design-space dimensionality reduction. Distributed configurations cover glider and airfoil problems for PME, PI-PME, and PD-PME, and a propeller case for PME. The complete-database RAE2822 regression uses an archived dataset [@Serani2026Airfoil] and compares the released solvers with the preceding implementation and an independent symmetric reference. After the documented filters, it uses 8,516 samples for PME and 7,391 for PI-PME and PD-PME. Checks cover retained dimensions, explained variance, resolved eigenvalues, weighted modes, and native reconstructions. Sign changes and rotations within repeated eigenspaces are handled explicitly in the comparisons.

The [verification protocol](https://cnr-inm-mao.github.io/pme-toolkit/reproducibility/) also includes controlled spectra, independent query designs, conditioning checks, and a streamed case with 1,048,576 observation coordinates and 64 construction samples. The latter uses generated observations with a small reference calculation; it assesses the implementation at large observation dimension. MATLAB/Python comparisons are integrated into continuous integration, and generated reports record source revisions, input checksums, and numerical settings.

Antoine DeBlois contributed a [Python snapshot solver](https://github.com/cnr-inm-mao/pme-toolkit/pull/1) in May 2026. Version 1.3.0 integrates this contribution into the common MATLAB/Python workflow. Kazuko Fuchi's [June 2026 report](https://github.com/cnr-inm-mao/pme-toolkit/issues/4) led to matching input checks in both languages: PI-PME and PD-PME now reject configurations without physical inputs before loading the database. Regression tests cover these errors, valid field-only and scalar-only inputs, and geometry-only PME.

The MIT-licensed [source code](https://github.com/cnr-inm-mao/pme-toolkit), [documentation](https://cnr-inm-mao.github.io/pme-toolkit/), and [Python distribution](https://pypi.org/project/pme-toolkit/1.3.0/) are publicly available. The version-specific archive is preserved on Zenodo [@Serani2026Toolkit].

# AI usage disclosure

OpenAI ChatGPT and Codex assisted debugging, refactoring, input validation, and regression testing of the existing MATLAB and Python implementations, focusing on numerical robustness and parity. Generative AI also supported documentation and manuscript preparation. The author made the scientific and architectural decisions, reviewed and edited the assisted material, and verified numerical behavior through comparisons with the preceding implementation, direct-snapshot regression tests, and MATLAB/Python parity checks. The author is responsible for the software, documentation, and manuscript.

# Acknowledgements

The author acknowledges the support of the Italian Ministry of University and Research (MUR) through the PRIN 2022 program, project BIODRONES (20227JNM52, CUP B53D23005560006), and the National Recovery and Resilience Plan (PNRR), Sustainable Mobility Center (CNMS), Spoke 3 Waterways (CN00000023, CUP B43C22000440001).

The author also acknowledges support from the U.S. Office of Naval Research (ONR) through the BEAM project, Grant No. N00014-26-1-2164, under the administration of Dr. Robert Brizzolara.

This work was also conducted within the NATO AVT-404 Research Task Group on “Enhanced Design Processes of Military Vehicles through Machine Learning Methods.”

The author thanks Antoine DeBlois for the contributed snapshot implementation and Kazuko Fuchi for feedback on physics-aware input validation.

# References
