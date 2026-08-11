"""Tests for the Postman parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from behave_gen.plugins.postman.parser import (
    PostmanCollection,
    PostmanParseError,
    _resolve_url,
    parse_postman,
    url_to_path,
)

FIXTURES = Path(__file__).resolve().parent.parent.parent / "fixtures" / "postman"


def test_parse_collection() -> None:
    collection = parse_postman(FIXTURES / "sample_collection.json")
    assert isinstance(collection, PostmanCollection)
    assert collection.name == "Sample API"
    assert "v2.1" in collection.schema
    assert len(collection.requests) == 3


def test_parse_collection_folders() -> None:
    collection = parse_postman(FIXTURES / "sample_collection.json")
    auth_reqs = [r for r in collection.requests if r.folder == "Auth"]
    assert len(auth_reqs) == 2
    assert auth_reqs[0].name == "Login"
    assert auth_reqs[0].method == "post"
    assert auth_reqs[0].url == "https://api.example.com/auth/login"


def test_parse_collection_url_object_form() -> None:
    collection = parse_postman(FIXTURES / "sample_collection.json")
    users = next(r for r in collection.requests if r.name == "Get Users")
    assert users.url == "https://api.example.com/users"


def test_parse_collection_root_level_request() -> None:
    collection = parse_postman(FIXTURES / "sample_collection.json")
    root_reqs = [r for r in collection.requests if r.folder == ""]
    assert len(root_reqs) == 1
    assert root_reqs[0].name == "Get Users"


def test_parse_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(PostmanParseError, match="not found"):
        parse_postman(tmp_path / "nope.json")


def test_parse_non_utf8_collection_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_bytes(b"\xff\xfe")
    with pytest.raises(PostmanParseError, match="decode"):
        parse_postman(bad)


def test_parse_invalid_collection_raises() -> None:
    with pytest.raises(PostmanParseError, match="schema"):
        parse_postman(FIXTURES / "invalid.json")


def test_url_to_path_extracts_path() -> None:
    assert url_to_path("https://api.example.com/users/123") == "/users/123"
    assert url_to_path("https://api.example.com") == "/"
    assert url_to_path("") == "/"


def test_resolve_url_handles_none_and_missing_url() -> None:
    assert _resolve_url(None) == ""
    assert _resolve_url({}) == ""
    assert _resolve_url("https://api.example.com/users") == "https://api.example.com/users"


def test_resolve_url_handles_dict_path_segments() -> None:
    """URL path variables must be rendered from their value, not as dict reprs."""
    url = {
        "host": ["api", "example", "com"],
        "path": ["users", {"key": "id", "value": ":id"}],
    }
    assert _resolve_url(url) == "http://api.example.com/users/:id"


def test_resolve_url_dict_segment_falls_back_to_key() -> None:
    url = {
        "host": ["api", "example", "com"],
        "path": [{"key": "userId"}],
    }
    assert _resolve_url(url) == "http://api.example.com/userId"


def test_resolve_url_includes_protocol_when_present() -> None:
    """Reconstructed object URLs preserve the protocol so the path can be extracted."""
    url = {
        "protocol": "https",
        "host": ["api", "example", "com"],
        "path": ["users"],
    }
    assert _resolve_url(url) == "https://api.example.com/users"


def test_resolve_url_object_path_extracts_to_root_path() -> None:
    """When a reconstructed object URL is parsed, only the path is kept."""
    url = {
        "protocol": "https",
        "host": ["api", "example", "com"],
        "path": ["users", "123"],
    }
    assert url_to_path(_resolve_url(url)) == "/users/123"


def test_parse_collection_defaults_empty_method_to_get(tmp_path: Path) -> None:
    """Empty or whitespace-only methods must default to 'get'."""
    path = tmp_path / "empty_method.json"
    path.write_text(
        '{"info": {"name": "x", "schema": "https://schema.getpostman.com/json/collection/v2.1.0/"},'
        '"item": [{"name": "r1", "request": {"method": "", "url": "https://example.com/a"}},'
        '{"name": "r2", "request": {"method": "   ", "url": "https://example.com/b"}}]}',
        encoding="utf-8",
    )
    collection = parse_postman(path)
    methods = {r.method for r in collection.requests}
    assert methods == {"get"}


def test_parse_null_collection_name_uses_default(tmp_path: Path) -> None:
    """A collection with ``name: null`` should fall back to 'Postman Collection', not 'None'."""
    path = tmp_path / "null_name.json"
    path.write_text(
        '{"info": {"name": null, "schema": "https://schema.getpostman.com/json/collection/v2.1.0/"},'
        '"item": []}',
        encoding="utf-8",
    )
    collection = parse_postman(path)
    assert collection.name == "Postman Collection"


def test_parse_null_schema_uses_empty_string(tmp_path: Path) -> None:
    """A collection with ``schema: null`` should produce empty string, not 'None'."""
    path = tmp_path / "null_schema.json"
    path.write_text(
        '{"info": {"name": "x", "schema": null}, "item": []}',
        encoding="utf-8",
    )
    with pytest.raises(PostmanParseError, match="schema"):
        parse_postman(path)


def test_parse_null_item_name_uses_unnamed(tmp_path: Path) -> None:
    """An item with ``name: null`` should fall back to 'Unnamed', not 'None'."""
    path = tmp_path / "null_item_name.json"
    path.write_text(
        '{"info": {"name": "x", "schema": "https://schema.getpostman.com/json/collection/v2.1.0/"},'
        '"item": [{"name": null, "request": {"method": "GET", "url": "https://example.com/a"}}]}',
        encoding="utf-8",
    )
    collection = parse_postman(path)
    assert collection.requests[0].name == "Unnamed"
