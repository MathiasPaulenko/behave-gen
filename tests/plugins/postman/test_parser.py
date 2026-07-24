"""Tests for the Postman parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from behave_gen.plugins.postman.parser import (
    PostmanCollection,
    PostmanParseError,
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
