"""behave-gen: CLI toolkit for scaffolding and evolving Behave BDD projects."""

from __future__ import annotations

import importlib.metadata as _metadata

try:
    __version__ = _metadata.version("behave-gen")
except _metadata.PackageNotFoundError:  # pragma: no cover - fallback for source-only runs.
    __version__ = "1.1.3"

__all__ = ["__version__"]
