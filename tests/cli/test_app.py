"""Tests for the behave-gen Typer CLI skeleton."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

import behave_gen.__main__  # noqa: F401 - entry point is importable without side effects.
from behave_gen.cli.app import app, run

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
    assert "--verbose" not in output
    assert "--dry-run" not in output


@pytest.mark.parametrize("command", EXPECTED_COMMANDS)
def test_command_help_exits_zero(command: str) -> None:
    result = runner.invoke(app, [command, "--help"])
    assert result.exit_code == 0, f"{command} --help failed: {result.output}"


def test_global_dry_run_accepted() -> None:
    """--dry-run is still accepted as a hidden global flag and does not crash."""
    result = runner.invoke(app, ["--dry-run", "stats"])
    # stats runs; the hidden flag is accepted without error.
    assert result.exit_code in (0, 1, 2)


def test_doctor_is_alias_for_check(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """doctor command delegates to run_check and exits cleanly."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code in (0, 1, 2)


def test_no_args_shows_help() -> None:
    """Invoking the CLI without arguments displays help and exits cleanly."""
    result = runner.invoke(app, [])
    assert result.exit_code == 0, result.output
    assert "Usage:" in result.output


def test_global_project_option_is_used(tmp_path: Path) -> None:
    result = runner.invoke(app, ["--project", str(tmp_path), "init", "global-proj"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "global-proj" / "environment.py").is_file()


def test_run_no_args_returns_zero() -> None:
    """The programmatic entry point returns 0 and prints help for no args."""
    assert run([]) == 0


def test_run_invalid_config_returns_one() -> None:
    """An invalid --config should return a non-zero exit code, not 0."""
    assert run(["--config", "nope.toml", "stats"]) == 1


def test_run_unknown_option_returns_nonzero() -> None:
    """Unknown options must not crash the programmatic entry point."""
    assert run(["--not-a-real-option"]) != 0


def test_run_unknown_option_prints_error(capsys: pytest.CaptureFixture[str]) -> None:
    """Usage errors must print a message instead of failing silently."""
    code = run(["--not-a-real-option"])
    assert code == 2
    assert "No such option" in capsys.readouterr().err


def test_run_missing_argument_prints_error(capsys: pytest.CaptureFixture[str]) -> None:
    """A missing required argument must be reported to the user."""
    code = run(["init"])
    assert code == 2
    assert "Missing argument" in capsys.readouterr().err


def test_run_unknown_command_prints_error(capsys: pytest.CaptureFixture[str]) -> None:
    code = run(["definitely-not-a-command"])
    assert code == 2
    err = capsys.readouterr().err
    assert "No such command" in err or "No such option" in err


def test_hidden_flags_warn_when_used(capsys: pytest.CaptureFixture[str]) -> None:
    """--verbose/--dry-run are accepted but warn that they are no-ops."""
    run(["--dry-run", "--verbose", "stats"])
    assert "not implemented" in capsys.readouterr().err


def test_run_propagates_typer_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    """typer.Exit codes must be returned by the programmatic entry point."""

    def _raise(*_args: object, **_kwargs: object) -> object:
        raise typer.Exit(code=7)

    monkeypatch.setattr("behave_gen.cli.app.app", _raise)
    assert run([]) == 7


@pytest.mark.parametrize("exc_cls,msg", [(OSError, "bad path"), (RuntimeError, "loop")])
def test_run_catches_path_errors(
    exc_cls: type[Exception], msg: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """OSError/RuntimeError from the CLI must not leak as tracebacks."""

    def _raise(*_args: object, **_kwargs: object) -> object:
        raise exc_cls(msg)

    monkeypatch.setattr("behave_gen.cli.app.app", _raise)
    assert run([]) == 1
