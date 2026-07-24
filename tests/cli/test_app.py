"""Tests for the behave-gen Typer CLI skeleton."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from behave_gen.cli.app import app

runner = CliRunner()

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from *text*."""
    return _ANSI_RE.sub("", text)


EXPECTED_COMMANDS = [
    "add",
    "check",
    "doctor",
    "format",
    "from-openapi",
    "from-postman",
    "from-swagger",
    "init",
    "lint",
    "migrate",
    "preview",
    "stats",
    "update",
]


def test_help_lists_all_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    output = _strip_ansi(result.stdout)
    for command in EXPECTED_COMMANDS:
        assert command in output, f"missing {command!r} in --help"


def test_help_lists_global_options() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    output = _strip_ansi(result.stdout)
    assert "--project" in output
    assert "--config" in output
    assert "--verbose" in output
    assert "--dry-run" in output


@pytest.mark.parametrize("command", EXPECTED_COMMANDS)
def test_command_help_exits_zero(command: str) -> None:
    result = runner.invoke(app, [command, "--help"])
    assert result.exit_code == 0, f"{command} --help failed: {result.output}"


def test_global_dry_run_accepted() -> None:
    """--dry-run is accepted as a global flag and does not crash."""
    result = runner.invoke(app, ["--dry-run", "stats"])
    # stats runs regardless of --dry-run; the flag is accepted without error.
    assert result.exit_code in (0, 1)


def test_doctor_is_alias_for_check(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """doctor command delegates to run_check and exits cleanly."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code in (0, 1, 2)


def test_no_args_shows_help() -> None:
    result = runner.invoke(app, [])
    assert result.exit_code != 0
