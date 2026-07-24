"""Tests for generator base types."""

from __future__ import annotations

from pathlib import Path

from behave_gen.generators.base import GenerationResult


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
