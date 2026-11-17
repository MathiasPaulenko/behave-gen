"""Tests for generator base types."""

from __future__ import annotations

from pathlib import Path

from behave_gen.generators.base import GenerationResult, validate_feature_map


def test_generation_result_written_files() -> None:
    features = (Path("a.feature"), Path("b.feature"))
    steps = (Path("steps/http_steps.py"),)
    result = GenerationResult(features=features, steps=steps)
    assert result.written_files == (*features, *steps)


def test_generation_result_defaults() -> None:
    result = GenerationResult()
    assert result.features == ()
    assert result.steps == ()
    assert result.warnings == ()
    assert result.written_files == ()


def test_validate_feature_map_keeps_parseable() -> None:
    valid = "Feature: Ok\n  Scenario: S\n    Given something\n"
    kept, warnings = validate_feature_map({"ok": valid})
    assert kept == {"ok": valid}
    assert warnings == []


def test_validate_feature_map_drops_unparseable() -> None:
    """Unparseable generated features must be skipped with a warning."""
    kept, warnings = validate_feature_map({"bad": "this is not gherkin\n"})
    assert kept == {}
    assert len(warnings) == 1
    assert "bad.feature" in warnings[0]
