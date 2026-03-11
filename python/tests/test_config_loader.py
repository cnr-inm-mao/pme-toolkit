from pathlib import Path

from pme_toolkit.config_loader import load_config


def test_load_benchmark_style_config():
    repo_root = Path(__file__).resolve().parents[2]
    cfg_path = repo_root / "benchmarks" / "standard" / "pme" / "glider" / "case.json"
    cfg = load_config(cfg_path)
    assert isinstance(cfg, dict)
    assert "dataset" in cfg
