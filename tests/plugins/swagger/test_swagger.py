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
