import json
from pathlib import Path
import numpy as np


def backmapping(model, x, active_idx=None):
    """
    Perform PME backmapping from reduced variables x to original variables u.

    Parameters
    ----------
    model : PMEModel
        Trained PME model.
    x : array_like
        Reduced variables (Ndim,)
    active_idx : array_like or None
        Indices of active variables. If None all variables assumed active.

    Returns
    -------
    u : ndarray
        Reconstructed original variables.
    """

    x = np.asarray(x)

    if active_idx is None:
        u = model.inverse_full(x)
    else:
        u = model.inverse_active(x, active_idx)

    return u


def run_backmapping(model, x, output_file=None):
    """
    Run backmapping and optionally save result.
    """

    u = backmapping(model, x)

    if output_file is not None:
        output_file = Path(output_file)
        np.savetxt(output_file, u)

    return u
