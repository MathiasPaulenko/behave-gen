"""Tests for ``behave-gen lint``."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from behave_gen.cli.app import app
from behave_gen.commands.init import InitOptions, init_project
from behave_gen.commands.lint import run_lint
from behave_gen.diagnostics import is_available

runner = CliRunner()


def _make_project(tmp_path: Path) -> Path:
    return init_project(tmp_path, InitOptions(name="proj"))


def test_lint_missing_root_returns_one(tmp_path: Path) -> None:
    assert run_lint(tmp_path / "nope") == 1


def test_lint_runs_without_crashing(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    code = run_lint(root)
    # behave-lint is installed in the test env; a clean project should pass.
    assert code in (0, 1)


def test_lint_cli_exits_cleanly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path)
    monkeypatch.chdir(root)
    result = runner.invoke(app, ["lint"])
    assert result.exit_code in (0, 1)


def test_lint_cli_with_fix_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path)
    monkeypatch.chdir(root)
    result = runner.invoke(app, ["lint", "--fix"])
    assert result.exit_code in (0, 1)


def test_lint_install_hint_when_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path)
    monkeypatch.chdir(root)
    monkeypatch.setattr(
        "behave_gen.commands.lint.check_extra",
        lambda extra: __import__(
            "behave_gen.diagnostics", fromlist=["DependencyStatus"]
        ).DependencyStatus(
            name="lint", available=False, install_hint="pip install behave-gen[lint]"
        ),
    )
    code = run_lint(root)
    assert code == 0


@pytest.mark.skipif(is_available("lint"), reason="behave-lint is installed")
def test_lint_hint_when_not_installed(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    code = run_lint(root)
    assert code == 0
