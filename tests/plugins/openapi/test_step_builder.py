"""Tests for the OpenAPI step builder."""

from __future__ import annotations

from pathlib import Path

from behave_gen.plugins.openapi import build_steps
from behave_gen.plugins.openapi.parser import parse_openapi

FIXTURES = Path(__file__).resolve().parent.parent.parent / "fixtures" / "openapi"


def test_build_steps_renders_http_library() -> None:
    spec = parse_openapi(FIXTURES / "petstore.json")
    text = build_steps(spec, project_name="petstore")
    assert "from behave import given, then, when" in text
    assert "urllib.request" in text
    assert "petstore" in text


def test_build_steps_no_pass_skeletons() -> None:
    spec = parse_openapi(FIXTURES / "petstore.json")
    text = build_steps(spec, project_name="petstore")
    stripped = text.replace("bypass", "").replace("passlib", "")
    assert "\n    pass\n" not in stripped
