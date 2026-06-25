from __future__ import annotations

import os
from pathlib import Path

from bridge.config import load_config, model_home


def test_model_store_no_duplication_contract(monkeypatch: object, tmp_path: Path) -> None:
    monkeypatch.setenv("DEEPSEEK_MODEL_HOME", str(tmp_path))  # type: ignore[attr-defined]
    config = load_config()
    assert model_home(config) == tmp_path
    assert not Path("models").exists()


def test_config_loads() -> None:
    config = load_config()
    assert config["wake_word"] == "ok computer"
    assert os.path.exists("okcomputer.config.schema.json")
