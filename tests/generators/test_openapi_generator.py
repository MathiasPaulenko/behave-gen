"""Tests for the OpenAPI generator and from-openapi command."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from behave_model import parse_feature
from typer.testing import CliRunner

from behave_gen.cli.app import app
from behave_gen.commands.from_openapi import FromOpenApiOptions
from behave_gen.generators.openapi import OpenApiGenerator

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "openapi"

runner = CliRunner()


def test_generator_can_handle_valid_spec() -> None:
    gen = OpenApiGenerator()
    assert gen.can_handle(FIXTURES / "petstore.json") is True


def test_generator_can_handle_missing_file(tmp_path: Path) -> None:
    gen = OpenApiGenerator()
    assert gen.can_handle(tmp_path / "nope.json") is False


def test_generator_can_handle_invalid_doc() -> None:
    gen = OpenApiGenerator()
    assert gen.can_handle(FIXTURES / "invalid.txt") is False


def test_generator_can_handle_swagger2() -> None:
    gen = OpenApiGenerator()
    assert gen.can_handle(FIXTURES / "swagger2.json") is False


def test_generator_writes_feature_files(tmp_path: Path) -> None:
    gen = OpenApiGenerator()
    out = tmp_path / "out"
    result = gen.generate(FIXTURES / "petstore.json", out)
    assert len(result.features) == 3
    assert (out / "features" / "pets.feature").is_file()
    assert (out / "features" / "pets_petId.feature").is_file()
    assert (out / "features" / "users.feature").is_file()
    assert result.steps == ()


def test_generator_writes_step_lib_when_requested(tmp_path: Path) -> None:
    gen = OpenApiGenerator()
    out = tmp_path / "out"
    result = gen.generate(FIXTURES / "petstore.json", out, step_lib="http")
    assert len(result.steps) == 1
    assert (out / "features" / "steps" / "http_steps.py").is_file()
    content = (out / "features" / "steps" / "http_steps.py").read_text(encoding="utf-8")
    assert "urllib.request" in content


def test_generator_with_tag(tmp_path: Path) -> None:
    gen = OpenApiGenerator()
    out = tmp_path / "out"
    gen.generate(FIXTURES / "petstore.json", out, tag="api")
    content = (out / "features" / "pets.feature").read_text(encoding="utf-8")
    assert content.startswith("@api\nFeature:")


def test_generator_with_path_filter(tmp_path: Path) -> None:
    gen = OpenApiGenerator()
    out = tmp_path / "out"
    result = gen.generate(FIXTURES / "petstore.json", out, include_paths=["/pets"])
    assert len(result.features) == 1
    assert (out / "features" / "pets.feature").is_file()


def test_generator_with_method_filter(tmp_path: Path) -> None:
    gen = OpenApiGenerator()
    out = tmp_path / "out"
    result = gen.generate(FIXTURES / "petstore.json", out, include_methods=["get"])
    # 3 paths have GET: /pets, /pets/{petId}, /users
    assert len(result.features) == 3


def test_generator_no_matches_warns(tmp_path: Path) -> None:
    gen = OpenApiGenerator()
    out = tmp_path / "out"
    result = gen.generate(FIXTURES / "petstore.json", out, include_paths=["/nope"])
    assert result.features == ()
    assert "No operations matched" in result.warnings[0]


def test_generator_generated_features_parse_with_behave_model(tmp_path: Path) -> None:
    gen = OpenApiGenerator()
    out = tmp_path / "out"
    gen.generate(FIXTURES / "petstore.json", out)
    for feature_file in (out / "features").glob("*.feature"):
        parse_feature(feature_file.read_text(encoding="utf-8"), filename=str(feature_file))


def test_run_from_openapi_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    spec = FIXTURES / "petstore.json"
    result = runner.invoke(app, ["from-openapi", str(spec), "--out-dir", "gen"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "gen" / "features" / "pets.feature").is_file()


def test_run_from_openapi_default_out_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    spec = FIXTURES / "petstore.json"
    result = runner.invoke(app, ["from-openapi", str(spec)])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "gen" / "features" / "pets.feature").is_file()
    assert not (tmp_path / "gen" / "features" / "features").exists()


def test_run_from_openapi_rejects_unsupported_step_lib(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app, ["from-openapi", str(FIXTURES / "petstore.json"), "--step-lib", "auth"]
    )
    assert result.exit_code == 1
    assert "Only the 'http' step library" in result.output


def test_run_from_openapi_with_step_lib(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    spec = FIXTURES / "petstore.json"
    result = runner.invoke(
        app, ["from-openapi", str(spec), "--out-dir", "gen", "--step-lib", "http"]
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "gen" / "features" / "steps" / "http_steps.py").is_file()


def test_run_from_openapi_missing_spec(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["from-openapi", "nope.json"])
    assert result.exit_code == 1


def test_run_from_openapi_invalid_spec(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["from-openapi", str(FIXTURES / "invalid.txt")])
    assert result.exit_code == 1


def test_run_from_openapi_options_dataclass() -> None:
    opts = FromOpenApiOptions(spec="x.json", tag="api")
    assert opts.spec == "x.json"
    assert opts.tag == "api"
    assert opts.step_lib is None
    assert opts.include_paths == ()


def test_generated_feature_behave_dry_run(tmp_path: Path) -> None:
    gen = OpenApiGenerator()
    out = tmp_path / "out"
    gen.generate(FIXTURES / "petstore.json", out, step_lib="http")
    proc = subprocess.run(
        [sys.executable, "-m", "behave", "--dry-run", "--no-color"],
        cwd=out,
        capture_output=True,
        text=True,
        check=False,
    )
    assert "ConfigError" not in proc.stdout
    assert "ParseError" not in proc.stdout
