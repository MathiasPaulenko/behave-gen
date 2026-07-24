"""Smoke tests for the behave-gen package bootstrap."""

from __future__ import annotations

import behave_gen
from behave_gen.cli.app import run


def test_version_is_string() -> None:
    """The package exposes a string version."""
    assert isinstance(behave_gen.__version__, str)
    assert behave_gen.__version__


def test_run_help_exits_zero() -> None:
    """The CLI ``--help`` exits successfully."""
    assert run(["--help"]) == 0
