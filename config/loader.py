from functools import lru_cache
from pathlib import Path

import yaml

from config.models import DefaultConfig, GraphConfig

_CONFIG_DIR = Path(__file__).resolve().parent


def _deep_merge(base: dict, override: dict) -> None:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


@lru_cache(maxsize=1)
def load_default_config() -> DefaultConfig:
    path = _CONFIG_DIR / "default.yaml"
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    return DefaultConfig(**data)


@lru_cache(maxsize=16)
def load_graph_config(graph_name: str) -> GraphConfig:
    default = load_default_config()
    path = _CONFIG_DIR / "graphs" / f"{graph_name}.yaml"

    if not path.exists():
        merged = default.model_dump()
        return GraphConfig(**merged)

    with open(path) as f:
        graph_data = yaml.safe_load(f) or {}

    merged = default.model_dump()
    _deep_merge(merged, graph_data)
    return GraphConfig(**merged)
