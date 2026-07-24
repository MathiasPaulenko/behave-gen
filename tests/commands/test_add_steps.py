"""Tests for ``behave-gen add steps``."""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
from typer.testing import CliRunner

from behave_gen.cli.app import app
from behave_gen.commands.init import InitOptions, init_project
from behave_gen.commands.steps import AddStepsError, AddStepsOptions, add_steps

runner = CliRunner()


def _make_project(tmp_path: Path) -> Path:
    return init_project(tmp_path, InitOptions(name="proj"))


def test_add_steps_http_creates_file(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    path = add_steps(root, AddStepsOptions(lib="http"))
    assert path == (root / "features" / "steps" / "http_steps.py").resolve()
    assert path.is_file()
    content = path.read_text(encoding="utf-8")
    assert "from behave import given, then, when" in content
    assert "urllib.request" in content


def test_add_steps_auth_creates_file(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    path = add_steps(root, AddStepsOptions(lib="auth"))
    assert path.name == "auth_steps.py"
    content = path.read_text(encoding="utf-8")
    assert "from behave import given, then, when" in content
    assert "_Session" in content


def test_add_steps_no_pass_skeletons(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    for lib in ("http", "auth"):
        path = add_steps(root, AddStepsOptions(lib=lib))
        content = path.read_text(encoding="utf-8")
        # No function body should be just `pass`.
        assert "def step_impl" not in content  # behave snippet name avoided
        stripped = content.replace("bypass", "").replace("passlib", "")
        assert "\n    pass\n" not in stripped


def test_add_steps_unknown_lib_raises(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    with pytest.raises(AddStepsError, match="Unknown step library"):
        add_steps(root, AddStepsOptions(lib="nope"))


def test_add_steps_existing_file_raises(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    add_steps(root, AddStepsOptions(lib="http"))
    with pytest.raises(AddStepsError, match="already exists"):
        add_steps(root, AddStepsOptions(lib="http"))


def test_add_steps_missing_project_raises(tmp_path: Path) -> None:
    with pytest.raises(AddStepsError, match="Project root not found"):
        add_steps(tmp_path / "nope", AddStepsOptions(lib="http"))


def test_add_steps_rejects_output_file_outside_steps(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    outside = tmp_path / "outside.py"
    with pytest.raises(AddStepsError, match="must be inside steps directory"):
        add_steps(root, AddStepsOptions(lib="http"), output_file=outside)


def test_add_steps_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path)
    monkeypatch.chdir(root)
    result = runner.invoke(app, ["add", "steps", "--lib", "http"])
    assert result.exit_code == 0, result.output
    assert (root / "features" / "steps" / "http_steps.py").is_file()


def test_add_steps_cli_unknown_lib(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path)
    monkeypatch.chdir(root)
    result = runner.invoke(app, ["add", "steps", "--lib", "nope"])
    assert result.exit_code == 1
    assert "Unknown step library" in result.output


def test_generated_steps_import_cleanly(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    add_steps(root, AddStepsOptions(lib="http"))
    steps_file = root / "features" / "steps" / "http_steps.py"
    script = tmp_path / "import_check.py"
    script.write_text(
        "import importlib.util, sys\n"
        f"spec = importlib.util.spec_from_file_location('m', r'{steps_file}')\n"
        "assert spec is not None and spec.loader is not None\n"
        "m = importlib.util.module_from_spec(spec)\n"
        "sys.modules['m'] = m\n"
        "spec.loader.exec_module(m)\n"
        "print('ok')\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"import failed:\n{proc.stdout}\n{proc.stderr}"
    assert "ok" in proc.stdout


def test_sample_feature_runs_end_to_end_with_behave(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    add_steps(root, AddStepsOptions(lib="auth"))
    # Write a feature that uses the auth steps.
    feature = root / "features" / "session.feature"
    feature.write_text(
        textwrap.dedent(
            """
            Feature: Session
              Scenario: An authenticated session
                Given I have a session token "abc"
                Then I should be authenticated
                When I store the value "alice" as "user"
                Then the session value "user" should be "alice"
                When I clear the session
                Then I should not be authenticated
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, "-m", "behave", "--no-color"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"behave failed:\n{proc.stdout}\n{proc.stderr}"
    assert "1 scenario passed" in proc.stdout or "1 passed" in proc.stdout
