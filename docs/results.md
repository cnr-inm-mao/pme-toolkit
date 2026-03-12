# Visualization and Results

PME-toolkit provides MATLAB utilities to inspect and interpret the outcome of dimensionality reduction workflows based on PME, PI-PME, and PD-PME.

These visualization tools support both routine benchmark analysis and deeper interpretation of the reduced representation, including variance retention, modal structure, source-wise contributions, and reconstruction quality.

---

## Overview

After running a benchmark case with `run_pme`, the toolkit generates a report structure that can be used for post-processing and visualization.

Typical workflow:

```matlab
run_pme("benchmarks/glider/pme_glider.json")

load("output/report.mat")
```

The generated `report` structure can then be passed to the available plotting utilities.

---

## Available visualization utilities

The MATLAB implementation currently provides the following plotting functions:

* `pme.plot_scree_plot`
* `pme.plot_variance_retained`
* `pme.plot_modes`
* `pme.plot_variable_modes`
* `pme.plot_variance_by_source`
* `pme.plot_nmse_by_source`

These utilities help interpret PME reductions, especially when different information sources are combined in PI-PME and PD-PME workflows.

---

## Scree plot

The scree plot shows the decay of the modal content retained by the reduction and helps assess the intrinsic dimensionality of the problem.

Example:

```matlab
pme.plot_scree_plot(report)
```

This plot is useful to identify whether the relevant information is concentrated in a small number of modes or distributed gradually across the embedding.

Typical questions supported by this plot include:

* How fast does the modal content decay?
* Is there an elbow suggesting a natural truncation level?
* Does the reduction indicate a low-dimensional structure?

---

## Variance retained

The cumulative retained variance can be visualized as a function of the number of retained modes.

Example:

```matlab
pme.plot_variance_retained(report)
```

This plot helps determine how many reduced coordinates are needed to retain a target level of information.

Typical uses include:

* selecting the number of retained dimensions
* comparing different benchmark cases or formulations
* verifying whether a compact embedding is sufficient

---

## Global modal structure

The global PME modes can be visualized using:

```matlab
pme.plot_modes(report)
```

This utility helps inspect the structure of the dominant directions found by the reduction procedure.

Depending on the selected case and available outputs, these modes may represent dominant latent directions affecting geometry, variables, or other embedded sources.

---

## Variable contributions to modes

When the reduction includes design variables explicitly, the contribution of the original variables to the retained modes can be inspected using:

```matlab
pme.plot_variable_modes(report)
```

This plot is particularly useful for interpretability because it helps identify which original design variables are most strongly associated with each reduced coordinate.

This can support:

* qualitative interpretation of the embedding
* identification of dominant design drivers
* comparison between purely data-driven and physics-informed reductions

---

## Variance contribution by source

When multiple sources are included in the embedding, such as geometry, design variables, or physics-based quantities, the contribution of each source can be visualized through:

```matlab
pme.plot_variance_by_source(report)
```

This plot helps understand how the retained information is distributed across the different sources included in the reduction.

It is especially useful for PI-PME and PD-PME analyses, where the user may want to assess whether the embedding is mainly driven by geometry, by physical observables, or by a balance of both.

---

## Reconstruction error by source

Source-wise reconstruction quality can be visualized using:

```matlab
pme.plot_nmse_by_source(report)
```

This function reports the normalized mean square error for the different sources represented in the model.

This allows the user to check whether the reduced representation reconstructs all sources with comparable quality or whether some sources are reconstructed more accurately than others.

Typical uses include:

* evaluating trade-offs in reduced dimension selection
* assessing the balance of the embedding across heterogeneous data
* comparing alternative PME configurations

---

## Interpretation of the plots

The visualization utilities should not be interpreted independently from the benchmark context. In particular:

* a fast scree decay usually suggests a compact effective dimension
* high retained variance does not automatically imply low reconstruction error for every source
* source-wise variance and source-wise NMSE provide complementary views
* variable-mode plots are especially valuable for interpretability, not only for compression assessment

For this reason, it is recommended to inspect several plots together rather than relying on a single metric.

---

## Typical post-processing workflow

A typical sequence of post-processing steps is:

```matlab
run_pme("benchmarks/glider/pme_glider.json")

load("output/report.mat")

pme.plot_scree_plot(report)
pme.plot_variance_retained(report)
pme.plot_modes(report)
pme.plot_variable_modes(report)
pme.plot_variance_by_source(report)
pme.plot_nmse_by_source(report)
```

This provides a compact but informative overview of the quality and interpretability of the reduction.

---

## Relation with the report utility

The visualization functions are designed to work consistently with the toolkit reporting workflow.

In the current MATLAB implementation, plotting logic has been refactored into dedicated functions so that:

* visualization is modular
* figures can be generated independently
* plotting behavior is easier to maintain and extend

This separation improves code clarity and makes it easier to reuse the same visualization functions across benchmark cases.

---

## Recommended use in benchmark studies

For reproducible benchmark comparisons, it is recommended to report at least:

* scree plot
* cumulative variance retained
* variance contribution by source
* NMSE by source

When interpretability is a central objective, variable-mode plots should also be included.

These visual summaries are useful both for internal analyses and for figures prepared for publications or benchmark reports.

---

## Notes

The exact appearance and content of the plots depend on the information available in the generated `report` structure and on the selected workflow configuration.

For benchmark setup and execution, see the pages on:

* Benchmarks
* Datasets
* Reproducibility

