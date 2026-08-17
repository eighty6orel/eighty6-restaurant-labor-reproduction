"""Shared matplotlib defaults for reproduction figures."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from eighty6_repro.paths import figures_dir

plt.rcParams.update(
    {
        "figure.dpi": 140,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.titleweight": "medium",
    }
)


def save_fig(name: str, directory: Path | None = None) -> Path:
    directory = directory or figures_dir()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    return path
