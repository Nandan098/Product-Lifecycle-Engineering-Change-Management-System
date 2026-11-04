from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"


def database_path() -> Path:
    raw = os.getenv("PLM_DB_PATH", "data/plm_demo.db")
    path = Path(raw)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def project_path(*parts: str) -> Path:
    return PROJECT_ROOT.joinpath(*parts)
