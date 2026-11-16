---
title: "PME-toolkit: a reproducible framework for design-space dimensionality reduction in parametric shape optimization"
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

Shape optimization seeks improved designs by changing the parameters of a geometry and evaluating their performance through numerical simulations. When many parameters are involved, exploring the design space can require a large computational budget. PME-toolkit constructs reduced design spaces from collections of parameterized geometries and, optionally, associated simulation outputs. The resulting reduced coordinates describe dominant variations in the supplied observations and retain an analytical mapping to the original design parameters. Researchers can therefore generate new candidates through their existing geometry models.

The toolkit implements Parametric Model Embedding (PME) [@Serani2023PME], Physics-Informed PME (PI-PME), and Physics-Driven PME (PD-PME) [@Serani2025EWC]. These formulations use geometric observations, combined geometric and physical observations, or physical observations alone, respectively. Python and MATLAB implementations share case definitions, numerical conventions, reporting, and verification protocols. Version 1.3.0 provides direct and snapshot eigensolvers, together with a separate interface for observations read in blocks [@Serani2026Toolkit].

# Statement of need

Simulation-based design optimization combines expensive numerical models with parameterizations that may contain redundant or weakly influential directions. Dimensionality reduction can make the resulting search more manageable, but its usefulness depends on which variations are retained and how reduced designs are converted into admissible inputs for existing simulation workflows [@Serani2025Survey]. Retaining geometric variance alone may also be insufficient when performance depends on features represented more clearly by physical fields or scalar responses.

PME-toolkit serves researchers who need to construct, compare, and reuse such reduced spaces without replacing their geometry generators or simulation solvers. It couples weighted observations with their paired native design parameters, providing an affine backmap to those parameters rather than requiring a separate inverse regression. The software consolidates preprocessing, source weighting, dimensionality selection, projection, native reconstruction, and diagnostic plots in a reproducible workflow. The previously published PME formulations and their aerodynamic, hydrodynamic, and propeller applications provide the scientific basis for these operations [@SeraniAST; @Serani2024JMSE; @Gaggero2026AOR].

# State of the field

General-purpose libraries such as scikit-learn provide principal-component analysis and inverse transformations in the fitted feature space [@Pedregosa2011]. Geometry-oriented tools such as PyGeM provide parameterized deformation methods that can supply shape observations [@Tezzele2021PyGeM]. These capabilities are complementary to the workflow addressed here. PME-toolkit links weighted geometric and physical observations to the native parameters of the supplied geometry model, including parameter components that do not contribute directly to the reduction metric.

The software contribution is the integration and verification of this specialized workflow across MATLAB and Python. A dedicated toolkit allows the two implementations to expose the same input semantics, weighting conventions, backmapping behavior, and benchmark protocols, while remaining independent of a particular geometry or simulation package. It consequently complements existing numerical and geometry libraries through array-based interfaces, rather than introducing a replacement geometry engine or optimization framework.

# Software design

The case workflow separates data loading and filtering, preparation of active design variables, construction of observation weights, decomposition, and downstream analysis. JSON configurations specify data sources, variable bounds, physical quantities, filters, and the requested retained-variance fraction. PME, PI-PME, and PD-PME share these operations. Both implementations reject physics-aware configurations without physical inputs, preventing a requested PI-PME or PD-PME analysis from silently omitting its physical information. Small fixtures support installation checks, while larger engineering databases are retrieved from separately archived datasets.

Direct and snapshot decomposition operate on the same centered samples and diagonal metric. The direct solver uses a symmetric covariance matrix restricted to positive-weight observation rows; the snapshot solver uses a sample Gram matrix and recovers the modes from its eigenvectors. Automatic selection chooses the smaller eigenproblem. These alternatives share numerical-rank thresholds, retained-variance accounting, and the model interface used for projection, backmapping, reporting, and plotting. Diagonal weights are stored as vectors, avoiding a dense metric matrix. Native parameters have zero metric weight but remain in the recovered modes, preserving the analytical backmap.

This design addresses two distinct memory regimes. The standard case workflow holds its input database in memory. For larger observation dimensions, the streaming interface accepts repeatable row-block readers and accumulates the snapshot matrix without retaining the full observation array. A compact model stores the factors required for native backmapping; observation modes can optionally be written in a second pass. Projection of new observations uses construction means and consistent global weights; physics-aware projection requires the corresponding physical observations for each query. The dense sample Gram matrix remains a limitation when the number of construction samples is large, and streaming does not remove that limitation.

Numerical safeguards also delimit the interpretation of a reduced model. The retained-variance fraction uses the complete weighted trace, and mode selection retains an entire repeated-eigenvalue cluster when it intersects the requested threshold. Numerically unresolved modes are excluded and reported. Retained observation variance does not guarantee exact recovery of all native-parameter variations, satisfaction of parameter bounds, or physical feasibility. These quantities require separate assessment in the consuming design workflow.

# Research impact statement

PME-toolkit provides executable engineering cases and numerical verification materials for research on design-space dimensionality reduction. Distributed configurations cover glider and airfoil problems for PME, PI-PME, and PD-PME, and a propeller case for PME. The complete-database RAE2822 regression uses an archived dataset [@Serani2026Airfoil] and compares the released solvers with the preceding implementation and an independent symmetric reference. After the documented filters, it uses 8,516 samples for PME and 7,391 for PI-PME and PD-PME. Checks cover retained dimensions, explained variance, resolved eigenvalues, weighted modes, and native reconstructions. Sign changes and rotations within repeated eigenspaces are handled explicitly in the comparisons.

The [verification protocol](https://cnr-inm-mao.github.io/pme-toolkit/reproducibility/) also includes controlled spectra, independent query designs, conditioning checks, and a streamed case with 1,048,576 observation coordinates and 64 construction samples. The latter uses generated observations with a small reference calculation; it assesses the implementation at large observation dimension. MATLAB/Python comparisons are integrated into continuous integration, and generated reports record source revisions, input checksums, and numerical settings.

Public development has incorporated an external [snapshot implementation](https://github.com/cnr-inm-mao/pme-toolkit/pull/1) contributed in May 2026 and a [user-reported configuration issue](https://github.com/cnr-inm-mao/pme-toolkit/issues/4) raised in June 2026. Their integration in the maintained workflow includes corresponding tests in both languages. Together with versioned releases, contribution guidance, and documented support through GitHub issues, these provide concrete evidence of refinement through external use and feedback. The research contribution of the present release is a reusable and independently checkable implementation of the published methods, with materials for evaluating their numerical behavior and integrating native-parameter backmaps into existing design studies.

The MIT-licensed [source code](https://github.com/cnr-inm-mao/pme-toolkit), [documentation](https://cnr-inm-mao.github.io/pme-toolkit/), and [Python distribution](https://pypi.org/project/pme-toolkit/1.3.0/) are publicly available. The version-specific archive is preserved on Zenodo [@Serani2026Toolkit].

# Acknowledgements

The author acknowledges the support of the Italian Ministry of University and Research (MUR) through the PRIN 2022 program, project BIODRONES (20227JNM52, CUP B53D230055600), and the National Recovery and Resilience Plan (PNRR), Sustainable Mobility Center (CNMS), Spoke 3 Waterways (CN00000023, CUP B43C22000440001).

This work was also conducted within the NATO AVT-404 Research Task Group on “Enhanced Design Processes of Military Vehicles through Machine Learning Methods.”

The author thanks Antoine DeBlois for the contributed snapshot implementation and Kazuko Fuchi for feedback on physics-aware input validation.

# References
