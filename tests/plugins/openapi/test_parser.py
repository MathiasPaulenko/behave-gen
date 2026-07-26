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


def test_parse_non_utf8_spec_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_bytes(b"\xff\xfe")
    with pytest.raises(OpenApiParseError, match="decode"):
        parse_openapi(bad)


def test_parse_invalid_document_raises() -> None:
    with pytest.raises(OpenApiParseError, match="Expected a mapping"):
        parse_openapi(FIXTURES / "invalid.txt")


def test_parse_invalid_yaml_raises(tmp_path: Path) -> None:
    pytest.importorskip("yaml")
    bad = tmp_path / "bad.yaml"
    bad.write_text("not: [", encoding="utf-8")
    with pytest.raises(OpenApiParseError, match="Could not parse"):
        parse_openapi(bad)


def test_parse_invalid_json_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(OpenApiParseError, match="Could not parse"):
        parse_openapi(bad)


def test_parse_swagger_2_raises() -> None:
    with pytest.raises(OpenApiParseError, match="Unsupported OpenAPI version"):
        parse_openapi(FIXTURES / "swagger2.json")


def test_parse_json_numeric_openapi_version_accepted(tmp_path: Path) -> None:
    """JSON specs with a numeric 3.x version must be accepted."""
    path = tmp_path / "spec.json"
    path.write_text(
        '{"openapi": 3.0, "info": {"title": "t", "version": "1"}, "paths": {}}',
        encoding="utf-8",
    )
    spec = parse_openapi(path)
    assert spec.openapi_version.startswith("3.")


def test_parse_yaml_unquoted_openapi_version_accepted(tmp_path: Path) -> None:
    """YAML specs with an unquoted 3.x version must be accepted."""
    pytest.importorskip("yaml")
    path = tmp_path / "spec.yaml"
    path.write_text(
        "openapi: 3.0\ninfo:\n  title: t\n  version: '1'\npaths: {}\n",
        encoding="utf-8",
    )
    spec = parse_openapi(path)
    assert spec.openapi_version.startswith("3.")


def test_operation_id_falls_back_to_method_path() -> None:
    spec = parse_openapi(FIXTURES / "petstore.json")
    users_get = next(op for op in spec.operations if op.path == "/users")
    assert users_get.operation_id == "get_users"


def test_operation_tags_preserved() -> None:
    spec = parse_openapi(FIXTURES / "petstore.json")
    pets_get = next(op for op in spec.operations if op.path == "/pets" and op.method == "get")
    assert pets_get.tags == ("pets",)
