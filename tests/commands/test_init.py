"""Tests for ``behave-gen init``."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from behave_gen.cli.app import app
from behave_gen.commands.init import InitError, InitOptions, init_project

runner = CliRunner()


def _project_files(root: Path) -> set[str]:
    return {str(p.relative_to(root)).replace("\\", "/") for p in root.rglob("*") if p.is_file()}


def test_init_creates_project(tmp_path: Path) -> None:
    root = init_project(tmp_path, InitOptions(name="my-project"))
    assert root == (tmp_path / "my-project").resolve()
    files = _project_files(root)
    assert "features/.gitkeep" in files
    assert "features/steps/.gitkeep" in files
    assert "environment.py" in files
    assert "behave.toml" in files
    assert "pyproject.toml" in files
    assert "README.md" in files


def test_init_substitutes_project_name(tmp_path: Path) -> None:
    root = init_project(tmp_path, InitOptions(name="demo"))
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "# demo" in readme
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "demo"' in pyproject


def test_init_without_force_fails_on_existing(tmp_path: Path) -> None:
    init_project(tmp_path, InitOptions(name="proj"))
    with pytest.raises(InitError, match="already exists"):
        init_project(tmp_path, InitOptions(name="proj"))


def test_init_with_force_overwrites(tmp_path: Path) -> None:
    root = init_project(tmp_path, InitOptions(name="proj"))
    (root / "README.md").write_text("user edit", encoding="utf-8")
    init_project(tmp_path, InitOptions(name="proj", force=True))
    assert "user edit" not in (root / "README.md").read_text(encoding="utf-8")


def test_init_kit_wires_behave_kit(tmp_path: Path) -> None:
    root = init_project(tmp_path, InitOptions(name="proj", kit=True))
    env = (root / "environment.py").read_text(encoding="utf-8")
    assert "behave_kit" in env
    assert "setup_kit" in env


def test_init_data_wires_behave_data(tmp_path: Path) -> None:
    root = init_project(tmp_path, InitOptions(name="proj", data=True))
    env = (root / "environment.py").read_text(encoding="utf-8")
    assert "behave_data" in env
    assert "setup_data" in env


def test_init_kit_and_data(tmp_path: Path) -> None:
    root = init_project(tmp_path, InitOptions(name="proj", kit=True, data=True))
    env = (root / "environment.py").read_text(encoding="utf-8")
    assert "behave_kit" in env
    assert "behave_data" in env


def test_init_invalid_name_raises(tmp_path: Path) -> None:
    with pytest.raises(InitError, match="Invalid project name"):
        init_project(tmp_path, InitOptions(name="bad:name"))


def test_init_unknown_template_raises(tmp_path: Path) -> None:
    with pytest.raises(InitError, match="Unknown template"):
        init_project(tmp_path, InitOptions(name="proj", template="nope"))


def test_init_cli_creates_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "cli-proj"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "cli-proj" / "environment.py").is_file()


def test_init_cli_existing_without_force(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "proj"], catch_exceptions=False)
    result = runner.invoke(app, ["init", "proj"])
    assert result.exit_code == 1
    assert "already exists" in result.output


def test_generated_project_passes_behave_dry_run(tmp_path: Path) -> None:
    root = init_project(tmp_path, InitOptions(name="behaving"))
    # behave must be installed (it is a base dependency).
    proc = subprocess.run(
        [sys.executable, "-m", "behave", "--dry-run"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"behave --dry-run failed:\n{proc.stdout}\n{proc.stderr}"


def test_generated_code_passes_ruff(tmp_path: Path) -> None:
    root = init_project(tmp_path, InitOptions(name="linted"))
    proc = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "environment.py"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"ruff failed:\n{proc.stdout}\n{proc.stderr}"


def test_init_rejects_dot_names(tmp_path: Path) -> None:
    for name in (".", ".."):
        with pytest.raises(InitError, match="Invalid project name"):
            init_project(tmp_path, InitOptions(name=name))


def test_init_rejects_path_traversal(tmp_path: Path) -> None:
    with pytest.raises(InitError, match="Invalid project name"):
        init_project(tmp_path, InitOptions(name="../escape"))


def test_init_rejects_absolute_name(tmp_path: Path) -> None:
    with pytest.raises(InitError, match="Invalid project name"):
        init_project(tmp_path, InitOptions(name="C:/unsafe"))
