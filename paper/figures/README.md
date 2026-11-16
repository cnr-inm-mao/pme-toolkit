# Manuscript workflow figure

`pme_workflow.png` is used by `paper.md`. `pme_workflow.pdf` provides a vector
version with the dense scatter layer rasterized. The accompanying JSON records
the dataset checksum, configuration, sample identities, and retained variance.

To regenerate the figure, install this checkout and obtain `database.mat` from
the [RAE2822 dataset](https://doi.org/10.5281/zenodo.18958555):

```bash
python -m pip install -e ./python
python paper/figures/make_workflow_figure.py --database /path/to/database.mat
```

The script verifies the archived input checksum and fits the standard PME
airfoil case. It shows a two-coordinate view of the five-dimensional embedding
and uses all five coordinates for the native backmap. The highlighted design
is the first valid non-baseline construction sample, selected independently of
backmap error. Returned parameters are shown in their original archived units.
The figure does not assess independent prediction accuracy or execute a
geometry generator.

The database itself is not part of the manuscript assets.
