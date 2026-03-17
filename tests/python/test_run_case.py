from pathlib import Path

from pme_toolkit.run_case import run_case


def test_run_case_glider(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    case_json = repo_root / "benchmarks" / "standard" / "pme" / "glider" / "case.json"

    out = run_case(
        case_json,
        save_plots=True,
        n_modes_plot=2,
        print_text_report=False,
    )

    outdir = Path(out["outdir"])
    assert outdir.is_dir()

    assert (outdir / "report.mat").is_file()
    assert (outdir / "model.npz").is_file()

    assert (outdir / "scree_plot.png").is_file()
    assert (outdir / "variance_retained.png").is_file()
    assert (outdir / "nmse_by_source.png").is_file()
    assert (outdir / "variance_by_source.png").is_file()
    assert (outdir / "variable_modes_normalized.png").is_file()
