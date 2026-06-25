from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_config(path: Path = Path("okcomputer.config.json")) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("config root must be an object")
    return data


def model_home(config: dict[str, Any]) -> Path:
    override = str(config.get("model_store", {}).get("home_override", ""))
    if override:
        return Path(override)
    import os

    env = os.environ.get("DEEPSEEK_MODEL_HOME")
    if env:
        return Path(env)
    return Path.home() / ".local" / "share" / "okcomputer" / "models"


def resolve_model(config: dict[str, Any], name: str) -> Path:
    return model_home(config) / name
