"""Smoke tests for the behave-gen package bootstrap."""

from __future__ import annotations

import importlib.metadata as _metadata
import tomllib
from pathlib import Path

import behave_gen
from behave_gen.cli.app import run


def test_version_is_string() -> None:
    """The package exposes a string version."""
    assert isinstance(behave_gen.__version__, str)
    assert behave_gen.__version__


def test_version_fallback_matches_pyproject() -> None:
    """The fallback version in __init__.py must match the version in pyproject.toml."""
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    with pyproject.open("rb") as handle:
        data = tomllib.load(handle)
    pyproject_version = data["project"]["version"]

    # When installed, __version__ comes from metadata and may lag behind.
    # When not installed, the fallback is used. Verify the fallback matches.
    try:
        _metadata.version("behave-gen")
    except _metadata.PackageNotFoundError:
        assert behave_gen.__version__ == pyproject_version
    else:
        # Installed: verify the fallback constant in source matches pyproject.toml.
        source = (Path(__file__).resolve().parent.parent / "behave_gen" / "__init__.py").read_text(
            encoding="utf-8"
        )
        assert pyproject_version in source


def test_run_help_exits_zero() -> None:
    """The CLI ``--help`` exits successfully."""
    assert run(["--help"]) == 0
