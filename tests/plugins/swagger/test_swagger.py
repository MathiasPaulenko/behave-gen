"""Tests for the Swagger 2.0 to OpenAPI 3.x converter."""

from __future__ import annotations

from pathlib import Path

import pytest

from behave_gen.plugins.openapi.parser import OpenApiSpec
from behave_gen.plugins.swagger import SwaggerParseError, convert_swagger_to_openapi

_FIXTURES = Path(__file__).resolve().parent.parent.parent / "fixtures" / "swagger"


def test_convert_swagger_to_openapi_returns_spec() -> None:
    path = _FIXTURES / "petstore_swagger2.json"
    spec = convert_swagger_to_openapi(path)
    assert isinstance(spec, OpenApiSpec)
    assert spec.openapi_version.startswith("3.")
    assert len(spec.operations) > 0


def test_convert_missing_file_raises() -> None:
    with pytest.raises(SwaggerParseError, match="not found"):
        convert_swagger_to_openapi(_FIXTURES / "missing.json")


def test_convert_unsupported_version_raises(tmp_path: Path) -> None:
    path = tmp_path / "not-swagger.json"
    path.write_text('{"openapi": "3.0.0"}', encoding="utf-8")
    with pytest.raises(SwaggerParseError, match="Unsupported Swagger version"):
        convert_swagger_to_openapi(path)


def test_convert_swagger_numeric_float_version_accepted(tmp_path: Path) -> None:
    """JSON or YAML may parse an unquoted 2.0 as a float."""
    path = tmp_path / "swagger2.json"
    path.write_text(
        '{"swagger": 2.0, "info": {"title": "t", "version": "1"}, "paths": {}}',
        encoding="utf-8",
    )
    spec = convert_swagger_to_openapi(path)
    assert spec.openapi_version.startswith("3.")


def test_convert_swagger_yaml_unquoted_version_accepted(tmp_path: Path) -> None:
    """YAML specs with an unquoted 2.0 version must be accepted."""
    pytest.importorskip("yaml")
    path = tmp_path / "swagger2.yaml"
    path.write_text(
        "swagger: 2.0\ninfo:\n  title: t\n  version: '1'\npaths: {}\n",
        encoding="utf-8",
    )
    spec = convert_swagger_to_openapi(path)
    assert spec.openapi_version.startswith("3.")


def test_convert_swagger_numeric_non_two_version_rejected(tmp_path: Path) -> None:
    """A numeric version that is not exactly 2.0 must still be rejected."""
    path = tmp_path / "swagger2.json"
    path.write_text(
        '{"swagger": 2.1, "info": {"title": "t", "version": "1"}, "paths": {}}',
        encoding="utf-8",
    )
    with pytest.raises(SwaggerParseError, match="Unsupported Swagger version"):
        convert_swagger_to_openapi(path)
