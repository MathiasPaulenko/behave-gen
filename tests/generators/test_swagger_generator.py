"""Tests for the Swagger converter and from-swagger command."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from behave_model import parse_feature
from typer.testing import CliRunner

from behave_gen.cli.app import app
from behave_gen.generators.swagger import SwaggerGenerator
from behave_gen.paths import safe_parse_feature_filename
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
    spec = tmp_path / "petstore_swagger2.json"
    shutil.copy2(FIXTURES / "petstore_swagger2.json", spec)
    result = runner.invoke(app, ["from-swagger", str(spec), "--out-dir", "gen"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "gen" / "features" / "pets.feature").is_file()
    assert (tmp_path / "gen" / "features" / "pets_petId.feature").is_file()


def test_run_from_swagger_default_out_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    spec = tmp_path / "petstore_swagger2.json"
    shutil.copy2(FIXTURES / "petstore_swagger2.json", spec)
    result = runner.invoke(app, ["from-swagger", str(spec)])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "gen" / "features" / "pets.feature").is_file()
    assert not (tmp_path / "gen" / "features" / "features").exists()


def test_run_from_swagger_rejects_unsupported_step_lib(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    spec = tmp_path / "petstore_swagger2.json"
    shutil.copy2(FIXTURES / "petstore_swagger2.json", spec)
    result = runner.invoke(app, ["from-swagger", str(spec), "--step-lib", "auth"])
    assert result.exit_code == 1
    assert "Only the 'http' step library" in result.output


def test_run_from_swagger_with_step_lib(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    spec = tmp_path / "petstore_swagger2.json"
    shutil.copy2(FIXTURES / "petstore_swagger2.json", spec)
    result = runner.invoke(
        app,
        [
            "from-swagger",
            str(spec),
            "--out-dir",
            "gen",
            "--step-lib",
            "http",
        ],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "gen" / "features" / "steps" / "http_steps.py").is_file()


def test_generator_step_lib_uses_project_name(tmp_path: Path) -> None:
    gen = SwaggerGenerator()
    out = tmp_path / "out"
    gen.generate(
        FIXTURES / "petstore_swagger2.json", out, step_lib="http", project_name="MyProject"
    )
    content = (out / "features" / "steps" / "http_steps.py").read_text(encoding="utf-8")
    assert "HTTP step definitions for MyProject" in content


def test_run_from_swagger_with_tag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    spec = tmp_path / "petstore_swagger2.json"
    shutil.copy2(FIXTURES / "petstore_swagger2.json", spec)
    result = runner.invoke(
        app,
        [
            "from-swagger",
            str(spec),
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
    spec = tmp_path / "petstore.json"
    shutil.copy2(OPENAPI_FIXTURES / "petstore.json", spec)
    result = runner.invoke(app, ["from-swagger", str(spec)])
    assert result.exit_code == 1


def test_generated_swagger_features_parse(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    spec = tmp_path / "petstore_swagger2.json"
    shutil.copy2(FIXTURES / "petstore_swagger2.json", spec)
    runner.invoke(app, ["from-swagger", str(spec), "--out-dir", "gen"])
    for feature_file in (tmp_path / "gen" / "features").glob("*.feature"):
        parse_feature(
            feature_file.read_text(encoding="utf-8"),
            filename=safe_parse_feature_filename(feature_file),
        )


def test_swagger_generator_can_handle() -> None:
    generator = SwaggerGenerator()
    assert generator.can_handle(FIXTURES / "petstore_swagger2.json") is True
    assert generator.can_handle(OPENAPI_FIXTURES / "petstore.json") is False
    assert generator.can_handle(Path("/nonexistent/swagger.json")) is False
