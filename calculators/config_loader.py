from __future__ import annotations

from pathlib import Path

import yaml

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "market_rates.yaml"
_CACHE: dict | None = None


def load_market_rates() -> dict:
    global _CACHE
    if _CACHE is None:
        with _CONFIG_PATH.open(encoding="utf-8") as handle:
            _CACHE = yaml.safe_load(handle)
    return _CACHE


def get_project_type_config(project_type: str) -> dict:
    return load_market_rates()["project_types"][project_type]


def get_region_config(region: str) -> dict:
    return load_market_rates()["regions"][region]


def get_phases() -> dict:
    return load_market_rates()["phases"]


def get_staff_roles() -> dict:
    return load_market_rates()["staff_roles"]


def get_drawing_disciplines() -> dict:
    return load_market_rates()["drawing_disciplines"]


def get_complexity_multipliers() -> dict:
    return load_market_rates()["complexity_multipliers"]


def get_overhead_multiplier() -> float:
    return float(load_market_rates()["overhead_multiplier"])
