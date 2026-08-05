"""Resolve the repository root for Code Ocean and local layouts.

On Code Ocean, ``/code`` is this package tree and the capsule root (``/``) holds
``data/``, ``docs/``, ``results/``, etc. Locally the same relative layout applies:
``code/_paths.py`` → parents include the repo root that contains ``data/raw``.

Generated analysis outputs (claims, reports, tempsweep) always go under
``results/``. Frozen datasets and ground truth stay under ``data/``.
"""
from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    here = Path(__file__).resolve().parent
    for p in [here, *here.parents]:
        if (p / "data" / "raw").is_dir():
            return p
    raise RuntimeError(
        "repo root not found (expected a parent directory containing data/raw/)"
    )


def code_root() -> Path:
    """Directory that holds analysis/, capture/, render/, config/ (this package)."""
    return Path(__file__).resolve().parent


def results_dir() -> Path:
    """Writable outputs directory (Code Ocean /results; locally <repo>/results)."""
    d = repo_root() / "results"
    d.mkdir(parents=True, exist_ok=True)
    return d
