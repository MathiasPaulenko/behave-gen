"""Tests for ``behave-gen migrate`` command."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from behave_gen.cli.app import app
from behave_gen.commands.migrate import MigrateOptions

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "cucumber"

runner = CliRunner()


def test_run_migrate_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["migrate", str(FIXTURES), "--out-dir", "gen"])
    assert result.exit_code == 0, result.output
    assert (
        tmp_path / "gen" / "features" / "src" / "test" / "resources" / "features" / "login.feature"
    ).is_file()


def test_run_migrate_missing_source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["migrate", "nope"])
    assert result.exit_code == 1


def test_run_migrate_options_dataclass() -> None:
    opts = MigrateOptions(source="src", out_dir="out")
    assert opts.source == "src"
    assert opts.out_dir == "out"
