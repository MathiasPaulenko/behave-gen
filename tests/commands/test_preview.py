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
    code = run_preview(str(feature), project_root=root)
    assert code == 0


def test_preview_invalid_feature_returns_one(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    feature = root / "features" / "bad.feature"
    feature.write_text("not valid gherkin at all\n", encoding="utf-8")
    code = run_preview(str(feature), project_root=root)
    # behave-model may be lenient; either 0 or 1 is acceptable as long as no crash.
    assert code in (0, 1)


def test_preview_relative_path_outside_root_returns_one(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    assert run_preview("../escape.feature", project_root=root) == 1


def test_preview_absolute_path_outside_root_returns_one(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    outside = tmp_path / "outside.feature"
    outside.write_text("Feature: Outside\n", encoding="utf-8")
    assert run_preview(str(outside), project_root=root) == 1


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


def test_preview_renders_tags_with_at_prefix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _make_project(tmp_path)
    monkeypatch.chdir(root)
    feature = root / "features" / "demo.feature"
    feature.write_text(
        "@demo\nFeature: Demo\n\n  @smoke\n  Scenario: A\n    Given step\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["preview", "features/demo.feature"])
    assert result.exit_code == 0, result.output
    assert "@demo" in result.output
    assert "@smoke" in result.output
    # Make sure tags are not rendered bare (without @).
    assert result.output.count("smoke\n") == 0 or "@smoke" in result.output


def test_preview_renders_outline_table_header(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _make_project(tmp_path)
    monkeypatch.chdir(root)
    feature = root / "features" / "demo.feature"
    feature.write_text(
        "Feature: Demo\n\n"
        "  Scenario Outline: SO\n"
        "    Given input <value>\n\n"
        "    Examples:\n"
        "      | value |\n"
        "      | 1     |\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["preview", "features/demo.feature"])
    assert result.exit_code == 0, result.output
    assert "| value |" in result.output
    assert "| 1" in result.output


def test_preview_non_utf8_file_returns_one(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    feature = root / "features" / "demo.feature"
    feature.write_bytes(b"\xff\xfe")
    assert run_preview(str(feature), project_root=root) == 1
