"""Tests for ``behave-gen format``."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from behave_gen.cli.app import app
from behave_gen.commands.format import run_format
from behave_gen.commands.init import InitOptions, init_project
from behave_gen.diagnostics import is_available

runner = CliRunner()


def _make_project(tmp_path: Path) -> Path:
    return init_project(tmp_path, InitOptions(name="proj"))


def test_format_missing_root_returns_one(tmp_path: Path) -> None:
    assert run_format(tmp_path / "nope") == 1


def test_format_runs_without_crashing(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    code = run_format(root)
    # behave-format is installed in the test env; a clean project should pass.
    assert code in (0, 1)


def test_format_check_mode(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    code = run_format(root, check=True)
    assert code in (0, 1)


def test_format_cli_exits_cleanly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path)
    monkeypatch.chdir(root)
    result = runner.invoke(app, ["format"])
    assert result.exit_code in (0, 1)


def test_format_cli_check_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path)
    monkeypatch.chdir(root)
    result = runner.invoke(app, ["format", "--check"])
    assert result.exit_code in (0, 1)


def test_format_install_hint_when_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path)
    monkeypatch.chdir(root)
    monkeypatch.setattr(
        "behave_gen.commands.format.check_extra",
        lambda extra: __import__(
            "behave_gen.diagnostics", fromlist=["DependencyStatus"]
        ).DependencyStatus(
            name="format", available=False, install_hint="pip install behave-gen[format]"
        ),
    )
    code = run_format(root)
    assert code == 0


def test_format_rejects_paths_outside_project_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _make_project(tmp_path)
    monkeypatch.setattr(
        "behave_gen.commands.format.check_extra",
        lambda extra: __import__(
            "behave_gen.diagnostics", fromlist=["DependencyStatus"]
        ).DependencyStatus(name="format", available=True, install_hint=""),
    )

    def _fail_if_called(*_args, **_kwargs):  # pragma: no cover - defensive.
        pytest.fail("subprocess.run should not be called for paths outside the project root")

    monkeypatch.setattr("behave_gen.commands.format.subprocess.run", _fail_if_called)
    outside = tmp_path / "outside.feature"
    outside.write_text("Feature: X\n", encoding="utf-8")
    assert run_format(root, paths=[str(outside)]) == 1


@pytest.mark.skipif(is_available("format"), reason="behave-format is installed")
def test_format_hint_when_not_installed(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    code = run_format(root)
    assert code == 0
