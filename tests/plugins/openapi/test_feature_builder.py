"""Tests for the OpenAPI feature builder."""

from __future__ import annotations

from pathlib import Path

from behave_model import parse_feature

from behave_gen.plugins.openapi import build_features
from behave_gen.plugins.openapi.parser import parse_openapi

FIXTURES = Path(__file__).resolve().parent.parent.parent / "fixtures" / "openapi"


def _spec() -> object:
    return parse_openapi(FIXTURES / "petstore.json")


def test_build_features_groups_by_path() -> None:
    features = build_features(_spec())  # type: ignore[arg-type]
    assert set(features.keys()) == {"pets", "pets_petId", "users"}


def test_build_features_content_parses() -> None:
    features = build_features(_spec())  # type: ignore[arg-type]
    for filename, content in features.items():
        feature = parse_feature(content, filename=f"{filename}.feature")
        assert feature.name


def test_build_features_pets_has_two_scenarios() -> None:
    features = build_features(_spec())  # type: ignore[arg-type]
    feature = parse_feature(features["pets"], filename="pets.feature")
    assert len(feature.scenarios) == 2


def test_build_features_with_tag() -> None:
    features = build_features(_spec(), tag="api")  # type: ignore[arg-type]
    assert features["pets"].startswith("@api\nFeature:")


def test_build_features_include_paths_filter() -> None:
    features = build_features(_spec(), include_paths=["/pets"])  # type: ignore[arg-type]
    assert set(features.keys()) == {"pets"}


def test_build_features_include_methods_filter() -> None:
    features = build_features(_spec(), include_methods=["get"])  # type: ignore[arg-type]
    # /pets (get), /pets/{petId} (get), /users (get)
    assert set(features.keys()) == {"pets", "pets_petId", "users"}
    for content in features.values():
        assert "GET" in content
        assert "POST" not in content
        assert "DELETE" not in content


def test_build_features_no_matches_returns_empty() -> None:
    features = build_features(_spec(), include_paths=["/nonexistent"])  # type: ignore[arg-type]
    assert features == {}


def test_build_features_scenario_uses_http_step_syntax() -> None:
    features = build_features(_spec())  # type: ignore[arg-type]
    content = features["pets"]
    assert 'When I send a GET request to "/pets"' in content
    assert 'When I send a POST request to "/pets"' in content
    assert "Then the response status should be 200" in content
