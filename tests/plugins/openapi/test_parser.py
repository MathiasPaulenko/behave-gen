"""Tests for the OpenAPI parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from behave_gen.plugins.openapi.parser import (
    OpenApiParseError,
    OpenApiSpec,
    parse_openapi,
)

FIXTURES = Path(__file__).resolve().parent.parent.parent / "fixtures" / "openapi"


def test_parse_json_spec() -> None:
    spec = parse_openapi(FIXTURES / "petstore.json")
    assert isinstance(spec, OpenApiSpec)
    assert spec.title == "Petstore API"
    assert spec.version == "1.0.0"
    assert spec.openapi_version == "3.0.3"
    assert len(spec.operations) == 5
    methods = {(op.method, op.path) for op in spec.operations}
    assert ("get", "/pets") in methods
    assert ("post", "/pets") in methods
    assert ("get", "/pets/{petId}") in methods
    assert ("delete", "/pets/{petId}") in methods


def test_parse_yaml_spec() -> None:
    pytest.importorskip("yaml")
    spec = parse_openapi(FIXTURES / "petstore.yaml")
    assert spec.title == "Petstore YAML API"
    assert len(spec.operations) == 3


def test_parse_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(OpenApiParseError, match="not found"):
        parse_openapi(tmp_path / "nope.json")


def test_parse_invalid_document_raises() -> None:
    with pytest.raises(OpenApiParseError, match="Expected a mapping"):
        parse_openapi(FIXTURES / "invalid.txt")


def test_parse_swagger_2_raises() -> None:
    with pytest.raises(OpenApiParseError, match="Unsupported OpenAPI version"):
        parse_openapi(FIXTURES / "swagger2.json")


def test_operation_id_falls_back_to_method_path() -> None:
    spec = parse_openapi(FIXTURES / "petstore.json")
    users_get = next(op for op in spec.operations if op.path == "/users")
    assert users_get.operation_id == "get_users"


def test_operation_tags_preserved() -> None:
    spec = parse_openapi(FIXTURES / "petstore.json")
    pets_get = next(op for op in spec.operations if op.path == "/pets" and op.method == "get")
    assert pets_get.tags == ("pets",)
