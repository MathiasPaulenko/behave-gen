"""Tests for the Swagger converter and from-swagger command."""

from __future__ import annotations

from pathlib import Path

import pytest
from behave_model import parse_feature
from typer.testing import CliRunner

from behave_gen.cli.app import app
from behave_gen.plugins.swagger import SwaggerParseError, convert_swagger_to_openapi

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "swagger"
OPENAPI_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "openapi"

runner = CliRunner()


def test_convert_swagger_to_openapi() -> None:
    spec = convert_swagger_to_openapi(FIXTURES / "petstore_swagger2.json")
    assert spec.title == "Swagger Petstore"
    assert spec.openapi_version == "3.0.3"
    assert len(spec.operations) == 3


def test_convert_swagger_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(SwaggerParseError, match="not found"):
        convert_swagger_to_openapi(tmp_path / "nope.json")


def test_convert_swagger_openapi_file_raises() -> None:
    with pytest.raises(SwaggerParseError, match="Unsupported Swagger version"):
        convert_swagger_to_openapi(OPENAPI_FIXTURES / "petstore.json")


def test_run_from_swagger_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app, ["from-swagger", str(FIXTURES / "petstore_swagger2.json"), "--out-dir", "gen"]
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "gen" / "features" / "pets.feature").is_file()
    assert (tmp_path / "gen" / "features" / "pets_petId.feature").is_file()


def test_run_from_swagger_with_step_lib(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        [
            "from-swagger",
            str(FIXTURES / "petstore_swagger2.json"),
            "--out-dir",
            "gen",
            "--step-lib",
            "http",
        ],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "gen" / "features" / "steps" / "http_steps.py").is_file()


def test_run_from_swagger_with_tag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        [
            "from-swagger",
            str(FIXTURES / "petstore_swagger2.json"),
            "--out-dir",
            "gen",
            "--tag",
            "api",
        ],
    )
    assert result.exit_code == 0, result.output
    content = (tmp_path / "gen" / "features" / "pets.feature").read_text(encoding="utf-8")
    assert content.startswith("@api\nFeature:")


def test_run_from_swagger_missing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["from-swagger", "nope.json"])
    assert result.exit_code == 1


def test_run_from_swagger_openapi_file_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["from-swagger", str(OPENAPI_FIXTURES / "petstore.json")])
    assert result.exit_code == 1


def test_generated_swagger_features_parse(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(
        app, ["from-swagger", str(FIXTURES / "petstore_swagger2.json"), "--out-dir", "gen"]
    )
    for feature_file in (tmp_path / "gen" / "features").glob("*.feature"):
        parse_feature(feature_file.read_text(encoding="utf-8"), filename=str(feature_file))
