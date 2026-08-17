"""Repository paths. Live extracts stay under data/ (gitignored)."""

from __future__ import annotations

from pathlib import Path

from eighty6_repro.config import REPO_ROOT


def repo_root() -> Path:
    return REPO_ROOT


def data_dir() -> Path:
    return REPO_ROOT / "data"


def raw_dir() -> Path:
    return data_dir() / "raw"


def extracts_dir() -> Path:
    return data_dir() / "extracts"


def output_dir() -> Path:
    return REPO_ROOT / "output"


def tables_dir() -> Path:
    return output_dir() / "tables"


def figures_dir() -> Path:
    return output_dir() / "figures"


def fixtures_dir() -> Path:
    return REPO_ROOT / "fixtures"


def expected_path() -> Path:
    return REPO_ROOT / "expected" / "headlines.json"


def ensure_output_dirs() -> None:
    for p in (raw_dir(), extracts_dir(), tables_dir(), figures_dir()):
        p.mkdir(parents=True, exist_ok=True)
