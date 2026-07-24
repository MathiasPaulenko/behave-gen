"""Tests for the Postman generator and from-postman command."""

from __future__ import annotations

from pathlib import Path

import pytest
from behave_model import parse_feature
from typer.testing import CliRunner

from behave_gen.cli.app import app
from behave_gen.generators.postman import PostmanGenerator

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "postman"

runner = CliRunner()


def test_generator_can_handle_valid_collection() -> None:
    gen = PostmanGenerator()
    assert gen.can_handle(FIXTURES / "sample_collection.json") is True


def test_generator_can_handle_missing_file(tmp_path: Path) -> None:
    gen = PostmanGenerator()
    assert gen.can_handle(tmp_path / "nope.json") is False


def test_generator_can_handle_invalid_collection() -> None:
    gen = PostmanGenerator()
    assert gen.can_handle(FIXTURES / "invalid.json") is False


def test_generator_writes_feature_files(tmp_path: Path) -> None:
    gen = PostmanGenerator()
    out = tmp_path / "out"
    result = gen.generate(FIXTURES / "sample_collection.json", out)
    assert len(result.features) == 2
    assert (out / "features" / "Auth.feature").is_file()
    assert (out / "features" / "Sample_API.feature").is_file()
    assert result.steps == ()


def test_generator_writes_step_lib_when_requested(tmp_path: Path) -> None:
    gen = PostmanGenerator()
    out = tmp_path / "out"
    result = gen.generate(FIXTURES / "sample_collection.json", out, step_lib="http")
    assert len(result.steps) == 1
    assert (out / "features" / "steps" / "http_steps.py").is_file()


def test_generator_with_tag(tmp_path: Path) -> None:
    gen = PostmanGenerator()
    out = tmp_path / "out"
    gen.generate(FIXTURES / "sample_collection.json", out, tag="api")
    content = (out / "features" / "Auth.feature").read_text(encoding="utf-8")
    assert content.startswith("@api\nFeature:")


def test_generator_generated_features_parse(tmp_path: Path) -> None:
    gen = PostmanGenerator()
    out = tmp_path / "out"
    gen.generate(FIXTURES / "sample_collection.json", out)
    for feature_file in (out / "features").glob("*.feature"):
        parse_feature(feature_file.read_text(encoding="utf-8"), filename=str(feature_file))


def test_run_from_postman_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app, ["from-postman", str(FIXTURES / "sample_collection.json"), "--out-dir", "gen"]
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "gen" / "features" / "Auth.feature").is_file()


def test_run_from_postman_with_step_lib(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        [
            "from-postman",
            str(FIXTURES / "sample_collection.json"),
            "--out-dir",
            "gen",
            "--step-lib",
            "http",
        ],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "gen" / "features" / "steps" / "http_steps.py").is_file()


def test_run_from_postman_missing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["from-postman", "nope.json"])
    assert result.exit_code == 1


def test_run_from_postman_invalid_collection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["from-postman", str(FIXTURES / "invalid.json")])
    assert result.exit_code == 1
