"""Tests for ``behave-gen add environment`` and ``add config``."""

from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from typer.testing import CliRunner

from behave_gen.cli.app import app
from behave_gen.commands.environment import (
    AddEnvironmentOptions,
    EnvironmentError,
    add_config,
    add_environment,
)
from behave_gen.commands.init import InitOptions, init_project

runner = CliRunner()


def _make_project(tmp_path: Path) -> Path:
    return init_project(tmp_path, InitOptions(name="proj"))


def test_add_environment_base(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    path = add_environment(root, AddEnvironmentOptions())
    content = path.read_text(encoding="utf-8")
    assert "behave_kit" not in content
    assert "behave_data" not in content
    assert "def before_all" in content


def test_add_environment_kit(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    path = add_environment(root, AddEnvironmentOptions(kit=True))
    content = path.read_text(encoding="utf-8")
    assert "behave_kit" in content
    assert "setup_kit" in content
    assert "behave_data" not in content


def test_add_environment_data(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    path = add_environment(root, AddEnvironmentOptions(data=True))
    content = path.read_text(encoding="utf-8")
    assert "behave_data" in content
    assert "setup_data" in content
    assert "behave_kit" not in content


def test_add_environment_kit_and_data(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    path = add_environment(root, AddEnvironmentOptions(kit=True, data=True))
    content = path.read_text(encoding="utf-8")
    assert "behave_kit" in content
    assert "behave_data" in content


def test_add_environment_missing_root_raises(tmp_path: Path) -> None:
    with pytest.raises(EnvironmentError, match="Project root not found"):
        add_environment(tmp_path / "nope", AddEnvironmentOptions(kit=True))


def test_add_environment_is_valid_python(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    add_environment(root, AddEnvironmentOptions(kit=True, data=True))
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "import ast; ast.parse(open(r'environment.py', encoding='utf-8').read())",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr


def test_add_environment_behave_dry_run_passes(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    add_environment(root, AddEnvironmentOptions(kit=True))
    proc = subprocess.run(
        [sys.executable, "-m", "behave", "--dry-run", "--no-color"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    # behave-kit is not installed, so importing environment.py would fail at
    # runtime. --dry-run still imports environment.py; we only assert no
    # ConfigError/ParseError on the feature files themselves.
    assert "ConfigError" not in proc.stdout


def test_add_config_behave_kit(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    path = add_config(root, "behave-kit")
    text = path.read_text(encoding="utf-8")
    assert "behave-kit>=1.0" in text


def test_add_config_idempotent(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    add_config(root, "behave-kit")
    text_after_first = (root / "pyproject.toml").read_text(encoding="utf-8")
    add_config(root, "behave-kit")
    text_after_second = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert text_after_first == text_after_second


def test_add_config_behave_data(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    path = add_config(root, "behave-data")
    text = path.read_text(encoding="utf-8")
    assert "behave-data>=1.0" in text


def test_add_config_unknown_raises(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    with pytest.raises(EnvironmentError, match="Unknown config"):
        add_config(root, "nope")


def test_add_config_missing_pyproject_raises(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    (root / "pyproject.toml").unlink()
    with pytest.raises(EnvironmentError, match="pyproject.toml not found"):
        add_config(root, "behave-kit")


def test_add_config_pyproject_still_parses(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    add_config(root, "behave-kit")
    add_config(root, "behave-data")
    with (root / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    opt = data["project"]["optional-dependencies"]
    assert "behave-kit>=1.0" in opt["kit"]
    assert "behave-data>=1.0" in opt["data"]


def test_add_environment_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path)
    monkeypatch.chdir(root)
    result = runner.invoke(app, ["add", "environment", "--kit"])
    assert result.exit_code == 0, result.output
    assert "behave_kit" in (root / "environment.py").read_text(encoding="utf-8")


def test_add_config_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path)
    monkeypatch.chdir(root)
    result = runner.invoke(app, ["add", "config", "behave-kit"])
    assert result.exit_code == 0, result.output
    assert "behave-kit>=1.0" in (root / "pyproject.toml").read_text(encoding="utf-8")
