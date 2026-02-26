from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


def load_settings(config_path: str) -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f) or {}
    if not isinstance(settings, dict):
        raise ValueError("El archivo de configuracion debe contener un objeto YAML.")
    return settings


def resolve_path(value: str, project_root: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (project_root / path).resolve()


def ensure_parent_dir(file_path: Path) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
