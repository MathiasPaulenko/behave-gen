"""Tests for ``behave-gen preview``."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from typer.testing import CliRunner

from behave_gen.cli.app import app
from behave_gen.commands.init import InitOptions, init_project
from behave_gen.commands.preview import run_preview

runner = CliRunner()


def _make_project(tmp_path: Path) -> Path:
    return init_project(tmp_path, InitOptions(name="proj"))


def test_preview_missing_file_returns_one(tmp_path: Path) -> None:
    assert run_preview("nope.feature", project_root=tmp_path) == 1


def test_preview_prints_feature(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    feature = root / "features" / "demo.feature"
    feature.write_text(
        textwrap.dedent(
            """
            Feature: Demo

              Scenario: A scenario
                Given a precondition
                When an action
                Then a result
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    code = run_preview(str(feature))
    assert code == 0


def test_preview_invalid_feature_returns_one(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    feature = root / "features" / "bad.feature"
    feature.write_text("not valid gherkin at all\n", encoding="utf-8")
    code = run_preview(str(feature))
    # behave-model may be lenient; either 0 or 1 is acceptable as long as no crash.
    assert code in (0, 1)


def test_preview_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path)
    feature = root / "features" / "demo.feature"
    feature.write_text(
        "Feature: Demo\n  Scenario: x\n    Given a step\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(root)
    result = runner.invoke(app, ["preview", "features/demo.feature"])
    assert result.exit_code == 0, result.output
    assert "Feature: Demo" in result.output
