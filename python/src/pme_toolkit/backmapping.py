from pathlib import Path

import numpy as np


def backmapping(model, alpha, active_idx=None):
    """
    Low-level PME backmapping from modal coordinates alpha to original variables.

    This helper expects reduced coordinates alpha in the PME modal space.
    It does not accept normalized x01 variables in [0,1]. For file-based
    backmapping from x01, use pme_toolkit.run_back.run_back or the pme-back CLI.

    Parameters
    ----------
    model : PmeModel
        Trained PME model.
    alpha : array_like
        Modal reduced coordinates with shape (n_samples, nconf) or (nconf,).
    active_idx : None
        Deprecated and unsupported. Active-variable indices are stored in model.uinfo.

    Returns
    -------
    u : ndarray
        Reconstructed full original variables.
    """
    if active_idx is not None:
        raise ValueError(
            "active_idx is deprecated and unsupported. "
            "Active-variable indices are stored in model.uinfo."
        )

    return model.inverse_full(np.asarray(alpha, dtype=float))


def run_backmapping(model, alpha, output_file=None):
    """
    Run low-level backmapping from alpha coordinates and optionally save result.
    """
    u = backmapping(model, alpha)

    if output_file is not None:
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        np.savetxt(output_file, u)

    return u
