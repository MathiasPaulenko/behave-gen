"""Tests for ``behave-gen migrate`` command."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from behave_gen.cli.app import app
from behave_gen.commands.init import InitOptions, init_project
from behave_gen.commands.migrate import MigrateOptions, run_migrate

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "cucumber"

runner = CliRunner()


def _copy_cucumber_fixtures(project: Path) -> str:
    """Copy the Cucumber fixture project into *project* and return the source path."""
    dest = project / "cucumber_src"
    shutil.copytree(FIXTURES, dest)
    return "cucumber_src"


def test_run_migrate_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project = init_project(tmp_path, InitOptions(name="proj"))
    monkeypatch.chdir(project)
    src = _copy_cucumber_fixtures(project)
    result = runner.invoke(app, ["migrate", src, "--out-dir", "gen"])
    assert result.exit_code == 0, result.output
    assert (
        project / "gen" / "features" / "src" / "test" / "resources" / "features" / "login.feature"
    ).is_file()


def test_run_migrate_default_out_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project = init_project(tmp_path, InitOptions(name="proj"))
    monkeypatch.chdir(project)
    src = _copy_cucumber_fixtures(project)
    result = runner.invoke(app, ["migrate", src])
    assert result.exit_code == 0, result.output
    assert (
        project
        / "migrated"
        / "features"
        / "src"
        / "test"
        / "resources"
        / "features"
        / "login.feature"
    ).is_file()


def test_run_migrate_missing_source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["migrate", "nope"])
    assert result.exit_code == 1


def test_run_migrate_options_dataclass() -> None:
    opts = MigrateOptions(source="src", out_dir="out")
    assert opts.source == "src"
    assert opts.out_dir == "out"


def test_run_migrate_rejects_relative_source_outside_project_root(tmp_path: Path) -> None:
    project = init_project(tmp_path, InitOptions(name="proj"))
    rc = run_migrate(
        MigrateOptions(source="../cucumber"),
        project_root=project,
    )
    assert rc == 1


def test_run_migrate_rejects_absolute_source_outside_project_root(tmp_path: Path) -> None:
    """An absolute source path outside the project root must be rejected."""
    project = init_project(tmp_path, InitOptions(name="proj"))
    rc = run_migrate(
        MigrateOptions(source=str(FIXTURES), out_dir="migrated"),
        project_root=project,
    )
    assert rc == 1


def test_run_migrate_outside_project_root_fails(tmp_path: Path) -> None:
    project = init_project(tmp_path, InitOptions(name="proj"))
    src = _copy_cucumber_fixtures(project)
    rc = run_migrate(
        MigrateOptions(source=src, out_dir=str(tmp_path)),
        project_root=project,
    )
    assert rc == 1


def test_run_migrate_resolves_absolute_out_dir_with_dotdot(tmp_path: Path) -> None:
    """An absolute out_dir with parent-directory components must be normalized."""
    project = init_project(tmp_path, InitOptions(name="proj"))
    src = _copy_cucumber_fixtures(project)
    out_dir = str(project / "migrated" / ".." / "migrated")
    rc = run_migrate(
        MigrateOptions(source=src, out_dir=out_dir),
        project_root=project,
    )
    assert rc == 0
    assert (project / "migrated" / "features").is_dir()


def test_run_migrate_destination_file_blocking_fails(tmp_path: Path) -> None:
    project = init_project(tmp_path, InitOptions(name="proj"))
    (project / "migrated" / "features").parent.mkdir(parents=True)
    (project / "migrated" / "features").write_text("", encoding="utf-8")
    src = _copy_cucumber_fixtures(project)
    rc = run_migrate(
        MigrateOptions(source=src),
        project_root=project,
    )
    assert rc == 1
