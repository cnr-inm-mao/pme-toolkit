"""Reproduce the JOSS workflow figure from the archived RAE2822 database.

Install this checkout with ``python -m pip install -e ./python``, then run::

    python paper/figures/make_workflow_figure.py --database PATH/database.mat

Dataset: https://doi.org/10.5281/zenodo.18958555
The database remains outside the manuscript assets. A single fit of the
standard PME case supplies the plotted shapes, scores, and native backmap.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
import numpy as np

from pme_toolkit.config_loader import load_case_json
from pme_toolkit.io import load_mat_database
from pme_toolkit.model import fit_model


ROOT = Path(__file__).resolve().parents[2]
DATABASE_SHA256 = "a662f691c90158503ad627d1e4c36edafe566ec2fedb2ef3cadaacbb509cc177"
BLUE = "#285f87"
ORANGE = "#b76419"
INK = "#202d37"
GRAY = "#6f7c87"


def prepare_data(database: Path) -> tuple[dict, dict]:
    digest = hashlib.sha256(database.read_bytes()).hexdigest()
    if digest != DATABASE_SHA256:
        raise ValueError("The database does not match the archived RAE2822 benchmark")
    db = load_mat_database(database)
    if db.shape != (410, 16385):
        raise ValueError(f"Unexpected database shape: {db.shape}")
    case = ROOT / "benchmarks/standard/pme/airfoil/case.json"
    cfg, _ = load_case_json(case)
    model = fit_model(db, cfg)
    ids = np.flatnonzero(model.filter_mask)
    query = int(np.flatnonzero(ids != cfg["baseline_col"])[0])
    shown = np.unique(np.r_[np.linspace(0, len(ids) - 1, 16, dtype=int), query])
    scores = model.alpha_train
    native = model.inverse_full(scores[[query]])[0]
    offset = model.inverse_full(np.zeros((1, model.nconf)))[0]
    modes = (model.inverse_full(np.eye(model.nconf)) - offset).T
    if not np.allclose(offset + modes @ scores[query], native, rtol=1e-13, atol=1e-14):
        raise ValueError("Native backmap factors do not reproduce inverse_full")
    total = float(np.sum(model.w[:, None] * model.pc**2) / len(ids))
    retained = float(np.sum(model.eigvals_reduced) / total)
    if (len(ids), model.nconf, len(native)) != (8516, 5, 20):
        raise ValueError("The standard benchmark dimensions have changed")
    data = {
        "geometry_x": db[:129, ids[shown]],
        "geometry_y": db[129:258, ids[shown]],
        "query_x": db[:129, ids[query]],
        "query_y": db[129:258, ids[query]],
        "scores": scores,
        "query": query,
        "native": native,
        "retained": retained,
    }
    provenance = {
        "dataset_doi": "10.5281/zenodo.18958555",
        "database_sha256": digest,
        "database_shape": list(db.shape),
        "case": str(case.relative_to(ROOT)),
        "case_sha256": hashlib.sha256(case.read_bytes()).hexdigest(),
        "samples": len(ids),
        "native_parameters": len(native),
        "retained_coordinates": model.nconf,
        "retained_geometric_variance": retained,
        "shown_original_columns_zero_based": ids[shown].tolist(),
        "highlighted_original_column_zero_based": int(ids[query]),
        "highlight_selection": "First retained non-baseline sample, independent of backmap error",
        "native_parameter_units": "Original archived values, not normalized values",
        "geometry_generator_executed": False,
    }
    return data, provenance


def style_axes(ax):
    ax.spines[["top", "right"]].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#a8b1b8")
        ax.spines[side].set_linewidth(0.6)
    ax.tick_params(width=0.6, length=2.5, pad=2, colors=GRAY)
    ax.grid(color="#e5e9ec", linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)


def draw_figure(data: dict, output: Path) -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9.5,
        "axes.labelsize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "text.color": INK,
        "axes.labelcolor": INK,
        "mathtext.fontset": "dejavusans",
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
        "savefig.facecolor": "white",
    })
    fig = plt.figure(figsize=(7.3, 2.95), facecolor="white")
    left = fig.add_axes([0.065, 0.30, 0.245, 0.38])
    middle = fig.add_axes([0.405, 0.28, 0.22, 0.43])
    right = fig.add_axes([0.735, 0.28, 0.235, 0.43])

    headings = [(0.065, "a", "Observed shapes"), (0.405, "b", "Reduced space"),
                (0.735, "c", "Native backmap")]
    for x, letter, title in headings:
        fig.text(x, 0.925, f"({letter})  {title}", fontsize=10.5, weight="bold")
    fig.text(0.065, 0.84, "8,516 samples · 20 parameters", fontsize=9)
    fig.text(0.405, 0.84, "5 reduced coordinates", fontsize=9)
    fig.text(0.405, 0.78, f"{100 * data['retained']:.2f}% variance", fontsize=9)
    fig.text(0.735, 0.84, "20 returned parameters", fontsize=9)
    fig.text(0.735, 0.77,
             r"$\widehat{\mathbf{u}}=\overline{\mathbf{u}}+\mathbf{V}_N\mathbf{x}$",
             fontsize=10)

    left.plot(data["geometry_x"], data["geometry_y"], color=BLUE,
              linewidth=0.6, alpha=0.38)
    left.plot(data["query_x"], data["query_y"], color=ORANGE, linewidth=1.3)
    left.set_xlim(-0.025, 1.025)
    left.set_ylim(-0.13, 0.13)
    left.set_aspect("equal", adjustable="box")
    left.set_xlabel("Chord coordinate")
    left.set_ylabel("Profile coordinate")
    left.set_xticks([0, 0.5, 1.0])
    left.set_yticks([-0.1, 0, 0.1])

    scores = data["scores"]
    middle.scatter(scores[:, 0], scores[:, 1], s=2.0, color=BLUE, alpha=0.20,
                   edgecolors="none", rasterized=True, zorder=2)
    q = scores[data["query"]]
    middle.scatter(q[0], q[1], s=32, color=ORANGE, edgecolors="white",
                   linewidth=0.6, zorder=5)
    middle.set_xlabel(r"$x_1$")
    middle.set_ylabel(r"$x_2$", rotation=0, labelpad=6)
    middle.set_xticks([-4, -2, 0, 2, 4])
    middle.set_yticks([-2, 0, 2])
    middle.margins(0.06)

    indices = np.arange(1, len(data["native"]) + 1)
    right.axhline(0, linewidth=0.7, color=GRAY, zorder=1)
    right.bar(indices, data["native"], width=0.7, color=ORANGE, alpha=0.85, zorder=3)
    right.set_xlabel(r"Parameter index $j$")
    right.set_ylabel(r"$\widehat{u}_j$", rotation=0, labelpad=7)
    right.set_xticks([1, 5, 10, 15, 20])
    right.set_xlim(0, 21)

    for ax in (left, middle, right):
        style_axes(ax)

    for start, end, label in [(0.325, 0.387, "PME"), (0.642, 0.718, "Backmap")]:
        fig.add_artist(FancyArrowPatch((start, 0.75), (end, 0.75),
                       transform=fig.transFigure, arrowstyle="-|>",
                       mutation_scale=9, linewidth=1, color=INK))
        fig.text((start + end) / 2, 0.80, label, ha="center", fontsize=9)

    fig.text(0.065, 0.08, "Orange: one construction sample", color=ORANGE, fontsize=9)
    fig.text(0.405, 0.08, "First two coordinates shown", fontsize=9)
    fig.text(0.735, 0.08, "All five coordinates used", fontsize=9)

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output.with_suffix(".png"), dpi=450, bbox_inches="tight", pad_inches=0.08)
    fig.savefig(output.with_suffix(".pdf"), bbox_inches="tight", pad_inches=0.08,
                metadata={"Title": "PME reduction and native backmap", "CreationDate": None})
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("pme_workflow"))
    args = parser.parse_args()
    data, provenance = prepare_data(args.database)
    draw_figure(data, args.output)
    args.output.with_suffix(".json").write_text(json.dumps(provenance, indent=2) + "\n")


if __name__ == "__main__":
    main()
