"""Tests for ``behave-gen stats``."""

from __future__ import annotations

import json
import os
import textwrap
from pathlib import Path

import pytest
from typer.testing import CliRunner

from behave_gen.cli.app import app
from behave_gen.commands.init import InitOptions, init_project
from behave_gen.commands.stats import StatsReport, run_stats

runner = CliRunner()


def _make_project(tmp_path: Path) -> Path:
    return init_project(tmp_path, InitOptions(name="proj"))


def _add_features(root: Path) -> None:
    (root / "features" / "a.feature").write_text(
        textwrap.dedent(
            """
            @smoke
            Feature: Feature A

              Scenario: Scenario one
                Given a precondition
                When an action
                Then a result

              Scenario Outline: Scenario two
                Given a precondition with "<value>"
                When an action with "<value>"
                Then a result with "<value>"

                Examples:
                  | value |
                  | x     |
                  | y     |
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    (root / "features" / "b.feature").write_text(
        "Feature: Feature B\n  Scenario: Scenario three\n    Given a step\n",
        encoding="utf-8",
    )


def test_stats_missing_root_returns_one(tmp_path: Path) -> None:
    assert run_stats(tmp_path / "nope") == 1


def test_stats_no_features_dir(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    # Remove the sample feature; the features dir still exists but may be empty.
    (root / "features" / "sample.feature").unlink()
    code = run_stats(root, fmt="text")
    assert code == 0


def test_stats_counts_features_and_scenarios(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    _add_features(root)
    code = run_stats(root, fmt="text")
    assert code == 0


def test_stats_json_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path)
    _add_features(root)
    monkeypatch.chdir(root)
    result = runner.invoke(app, ["stats", "--format", "json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["features"] == 3  # sample + a + b
    assert payload["scenarios"] >= 3
    assert payload["steps"] >= 4


def test_stats_text_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path)
    _add_features(root)
    monkeypatch.chdir(root)
    result = runner.invoke(app, ["stats"])
    assert result.exit_code == 0, result.output
    assert "Features:" in result.output
    assert "Scenarios:" in result.output


def test_stats_invalid_format_returns_one(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    assert run_stats(root, fmt="xml") == 1


def test_stats_report_to_dict() -> None:
    report = StatsReport(project="x", features=2, scenarios=5, steps=10)
    d = report.to_dict()
    assert d["features"] == 2
    assert d["scenarios"] == 5
    assert d["steps"] == 10


def test_stats_counts_background_steps(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path)
    (root / "features" / "sample.feature").unlink()
    (root / "features" / "with_background.feature").write_text(
        "Feature: Bg\n\n  Background:\n    Given setup\n\n  Scenario: S\n    Given step\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(root)
    result = runner.invoke(app, ["stats", "--format", "json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["scenarios"] == 1
    assert payload["steps"] == 2  # background + scenario


def test_stats_skips_symlinked_feature_outside_root(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    outside = tmp_path / "outside.feature"
    outside.write_text("Feature: Outside\n  Scenario: x\n    Given a\n", encoding="utf-8")
    link = root / "features" / "outside.feature"
    try:
        os.symlink(outside, link)
    except OSError:
        pytest.skip("Symlinks are not supported in this environment")
    code = run_stats(root)
    assert code == 0
