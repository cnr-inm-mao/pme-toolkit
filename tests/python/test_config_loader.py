from pathlib import Path

from pme_toolkit.config_loader import load_config


def test_load_benchmark_style_config() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    cfg_path = repo_root / "benchmarks" / "standard" / "pme" / "glider" / "case.json"

    cfg = load_config(cfg_path)

    assert isinstance(cfg, dict)
    assert cfg["mode"] == "pme"
    assert "geom" in cfg
    assert "vars" in cfg
    assert "io" in cfg
    assert Path(cfg["io"]["dbfile"]).is_absolute()
