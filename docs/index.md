<p align="left">
  <a href="https://cnr-inm-mao.github.io/pme-toolkit">
    <img src="assets/logos/logo-hori-nobg.png" width="300">
  </a>
</p>

# PME-toolkit

PME-toolkit is a framework for **design-space dimensionality reduction in parametric shape optimization**, based on:

- Parametric Model Embedding (PME)
- Physics-Informed PME (PI-PME)
- Physics-Driven PME (PD-PME)

The toolkit provides a **reproducible, data-driven workflow** to construct low-dimensional representations of high-dimensional parametric design spaces while preserving a direct link to the original variables.

**Python for daily use. MATLAB for reference validation.**

---

## Project status

PME-toolkit is a **released research software package (v1.2)**:

- [PyPI package (installable)](https://pypi.org/project/pme-toolkit/)
- [Zenodo archive (versioned, citable)](https://doi.org/10.5281/zenodo.18962859)
- [GitHub repository](https://github.com/cnr-inm-mao/pme-toolkit)
- submitted to JOSS (under review)

The Python implementation is fully functional and recommended for use.  
MATLAB remains available as a reference implementation for validation and comparison.

---

## What the toolkit does

PME-toolkit enables:

- reduction of high-dimensional parametric design spaces
- extraction of dominant modes of variability
- construction of interpretable latent representations
- reconstruction of original variables through backmapping
- reproducible benchmarking across methods and datasets

---

## Minimal workflow

A typical PME workflow consists of:

1. preparing input data (geometry, variables, optional physics)
2. defining a JSON configuration file
3. running the dimensionality reduction
4. analyzing results and visualizations
5. optionally performing backmapping

---

## Reproducibility and benchmarks

PME-toolkit is designed for **reproducible benchmarking across methods and datasets**.

Validated on:

- a **tiny self-contained glider case** (included in the repository)  
- **benchmark configurations** for airfoil and underwater glider geometries  
- **larger datasets** available via Zenodo  

All workflows are defined through **JSON configuration files**, ensuring full reproducibility of experiments.

---

## Why PME-toolkit?

PME-toolkit extends classical PCA-based approaches through a **generalized, weighted formulation** tailored to parametric design problems.

- **Analytical backmapping (core feature)**  
  Reduced coordinates can be mapped back exactly to the original parametric variables.

- **Generalized formulation with weights**  
  PME relies on a weighted POD/PCA formulation, where weights can encode the role of variables (including null weights).  
  This formulation is not equivalent to standard PCA and cannot be reduced to a simple SVD.

- **Design-aware latent space**  
  Unlike standard PCA (typically applied to state snapshots without variables), PME explicitly incorporates parametric design variables into the embedding.

- **Physics-aware variants**  
  PI-PME and PD-PME embed physical information into the dimensionality-reduction process.

Result: **interpretable and optimization-ready reduced spaces**.

---

## Key concepts

- **Embedding** → projection of the design space into a reduced latent space  
- **Modes** → principal directions of variability  
- **Retained variance** → fraction of variance captured by the reduced space  
- **Backmapping** → reconstruction of original variables from reduced coordinates  

---

## Documentation structure

- Quickstart → run the tool immediately  
- Workflow → full pipeline description  
- Input data → required data structure  
- Configuration → JSON specification  
- Benchmarks → predefined test cases  
- Datasets → dataset organization  
- Backmapping → reconstruction process  
- Visualization → interpretation of results  
- APIs → Python and MATLAB interfaces  
- Reproducibility → validation workflows  

---

## Philosophy

PME-toolkit is designed to support:

- reproducible research  
- transparent dimensionality reduction workflows  
- systematic comparison between methods  
- integration with optimization pipelines  

The toolkit follows a **configuration-driven approach**, where experiments are fully defined through JSON files and can be reproduced across environments.

---

## Citation

If you use PME-toolkit in your work, please cite the associated publication (see the *Citation* page).
