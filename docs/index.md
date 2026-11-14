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

This documentation covers the **v1.3.0 APIs** in MATLAB and Python, including
direct and snapshot eigensolvers and the advanced streamed observation API.
Published software versions and archives are available through:

- [PyPI package (installable)](https://pypi.org/project/pme-toolkit/)
- [Zenodo archive (versioned, citable)](https://doi.org/10.5281/zenodo.18962859)
- [GitHub repository](https://github.com/cnr-inm-mao/pme-toolkit)
- [GitHub releases](https://github.com/cnr-inm-mao/pme-toolkit/releases)

The Python implementation is fully functional and recommended for use.  
MATLAB remains available as a reference implementation for validation and comparison.
While v1.3.0 is being prepared, its new APIs require the corresponding source
checkout; the existing PyPI release does not yet provide them. See
[Quickstart](quickstart.md) for installation and [Reproducibility](reproducibility.md)
for the validation protocols.

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

The repository includes:

- a **tiny self-contained glider case** used by the local tests;
- benchmark configurations for airfoil, underwater glider and propeller data;
- a [complete Zenodo airfoil regression](zenodo-regression.md) for PME, PI-PME
  and PD-PME, comparing the preceding implementation and both current languages;
- [controlled streamed experiments](reproducibility.md) up to 1,048,576
  observation coordinates.

Standard case workflows are defined through JSON files. The advanced streaming
API accepts explicit observation readers, fixed weights and prepared native
variables; its reproducible examples include the required reader definitions.

---

## Why PME-toolkit?

PME-toolkit extends classical PCA-based approaches through a **generalized, weighted formulation** tailored to parametric design problems.

- **Analytical backmapping (core feature)**  
  Reduced coordinates are mapped analytically to native design variables.
  Recovering an original training design depends on the retained observation
  subspace and is not guaranteed after truncation.

- **Generalized formulation with weights**  
  PME relies on a weighted POD/PCA formulation, where weights can encode the role of variables (including null weights).  
  The observation metric and paired native-variable components are retained
  by both direct and snapshot solutions.

- **A shared fitting workflow**
  `solver="auto"` chooses between the direct observation covariance and the
  snapshot Gram matrix. Both use the same preprocessing, metric, numerical-rank
  policy and downstream model interface. See [Snapshot formulation](snapshot.md).

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

The standard toolkit workflow follows a **configuration-driven approach**,
with explicit datasets, preprocessing settings and solver choices.

---

## Citation

If you use PME-toolkit in your work, please cite the associated publication (see the *Citation* page).
