"""Tests for the OpenAPI feature builder."""

from __future__ import annotations

from pathlib import Path

import pytest
from behave_model import parse_feature

from behave_gen.plugins.openapi import build_features
from behave_gen.plugins.openapi.parser import OpenApiOperation, OpenApiSpec, parse_openapi

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


def test_build_features_with_comma_separated_tags() -> None:
    features = build_features(_spec(), tag="api,smoke")  # type: ignore[arg-type]
    assert features["pets"].startswith("@api @smoke\nFeature:")


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


def test_build_features_title_cases_multi_word_path() -> None:
    """Multi-word path segments should be title-cased in the feature name."""
    spec = OpenApiSpec(
        title="API",
        version="1.0",
        openapi_version="3.0.0",
        operations=(
            OpenApiOperation(
                path="/user_profile/settings",
                method="get",
                operation_id="x",
                summary="",
                tags=(),
            ),
        ),
    )
    features = build_features(spec)  # type: ignore[arg-type]
    content = features["user_profile_settings"]
    assert "Feature: User Profile Settings" in content


def test_build_features_disambiguates_colliding_filenames() -> None:
    """Different paths that sanitize to the same name must not overwrite each other."""
    spec = OpenApiSpec(
        title="Collision",
        version="1.0",
        openapi_version="3.0.0",
        operations=(
            OpenApiOperation(
                path="/users/{id}", method="get", operation_id="get_user", summary="", tags=()
            ),
            OpenApiOperation(
                path="/users_id", method="get", operation_id="get_users_id", summary="", tags=()
            ),
        ),
    )
    features = build_features(spec)  # type: ignore[arg-type]
    assert set(features.keys()) == {"users_id", "users_id_2"}


def test_build_features_sanitizes_multiline_summaries() -> None:
    """Newlines and other whitespace in summaries must not produce invalid Gherkin."""
    spec = OpenApiSpec(
        title="Whitespace",
        version="1.0",
        openapi_version="3.0.0",
        operations=(
            OpenApiOperation(
                path="/x",
                method="get",
                operation_id="x",
                summary="first line\nsecond line",
                tags=(),
            ),
        ),
    )
    features = build_features(spec)  # type: ignore[arg-type]
    content = features["x"]
    assert "first line second line" in content
    feature = parse_feature(content, filename="x.feature")
    assert feature.name


def test_build_features_avoids_windows_reserved_filenames(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Windows reserved device names must not be used as feature filenames."""
    monkeypatch.setattr("os.name", "nt")
    spec = OpenApiSpec(
        title="API",
        version="1.0",
        openapi_version="3.0.0",
        operations=(
            OpenApiOperation(
                path="/CON",
                method="get",
                operation_id="get_con",
                summary="",
                tags=(),
            ),
        ),
    )
    features = build_features(spec)  # type: ignore[arg-type]
    assert "CON_" in features
    assert "CON" not in features
