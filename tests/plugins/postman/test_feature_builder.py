"""Tests for the Postman feature builder."""

from __future__ import annotations

from pathlib import Path

import pytest
from behave_model import parse_feature

from behave_gen.plugins.postman import build_features
from behave_gen.plugins.postman.parser import PostmanCollection, PostmanRequest, parse_postman

FIXTURES = Path(__file__).resolve().parent.parent.parent / "fixtures" / "postman"


def _collection() -> object:
    return parse_postman(FIXTURES / "sample_collection.json")


def test_build_features_groups_by_folder() -> None:
    features = build_features(_collection())  # type: ignore[arg-type]
    assert "Auth" in features
    assert "Sample_API" in features  # root-level requests use collection name


def test_build_features_content_parses() -> None:
    features = build_features(_collection())  # type: ignore[arg-type]
    for filename, content in features.items():
        feature = parse_feature(content, filename=f"{filename}.feature")
        assert feature.name


def test_build_features_auth_has_two_scenarios() -> None:
    features = build_features(_collection())  # type: ignore[arg-type]
    feature = parse_feature(features["Auth"], filename="Auth.feature")
    assert len(feature.scenarios) == 2


def test_build_features_with_tag() -> None:
    features = build_features(_collection(), tag="api")  # type: ignore[arg-type]
    assert features["Auth"].startswith("@api\nFeature:")


def test_build_features_with_comma_separated_tags() -> None:
    features = build_features(_collection(), tag="api,smoke")  # type: ignore[arg-type]
    assert features["Auth"].startswith("@api @smoke\nFeature:")


def test_build_features_uses_http_step_syntax() -> None:
    features = build_features(_collection())  # type: ignore[arg-type]
    content = features["Auth"]
    assert 'When I send a POST request to "/auth/login"' in content
    assert "Then the response status should be 200" in content


def test_build_features_disambiguates_colliding_folders() -> None:
    """Different folder paths that sanitize to the same name must not overwrite each other."""
    collection = PostmanCollection(
        name="API",
        schema="https://schema.getpostman.com/json/collection/v2.1.0/",
        requests=(
            PostmanRequest(
                name="Login",
                method="post",
                url="https://api.example.com/auth/login",
                folder="Auth/Login",
            ),
            PostmanRequest(
                name="Reset",
                method="post",
                url="https://api.example.com/auth/login/reset",
                folder="Auth_Login",
            ),
        ),
    )
    features = build_features(collection)  # type: ignore[arg-type]
    assert set(features.keys()) == {"Auth_Login", "Auth_Login_2"}


def test_build_features_sanitizes_multiline_request_names() -> None:
    """Newlines and other whitespace in request names must not produce invalid Gherkin."""
    collection = PostmanCollection(
        name="API",
        schema="https://schema.getpostman.com/json/collection/v2.1.0/",
        requests=(
            PostmanRequest(
                name="Bad\nName",
                method="get",
                url="https://api.example.com/x",
                folder="",
            ),
        ),
    )
    features = build_features(collection)  # type: ignore[arg-type]
    content = features["API"]
    assert "Bad Name" in content
    feature = parse_feature(content, filename="API.feature")
    assert feature.name


def test_build_features_title_cases_multi_word_folder() -> None:
    """Multi-word folder names should be title-cased in the feature name."""
    collection = PostmanCollection(
        name="API",
        schema="https://schema.getpostman.com/json/collection/v2.1.0/",
        requests=(
            PostmanRequest(
                name="Login",
                method="post",
                url="https://api.example.com/auth/login",
                folder="user_profile/settings",
            ),
        ),
    )
    features = build_features(collection)  # type: ignore[arg-type]
    content = features["user_profile_settings"]
    assert "Feature: User Profile Settings" in content


def test_build_features_avoids_windows_reserved_filenames(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Windows reserved device names must not be used as feature filenames."""
    monkeypatch.setattr("os.name", "nt")
    collection = PostmanCollection(
        name="API",
        schema="https://schema.getpostman.com/json/collection/v2.1.0/",
        requests=(
            PostmanRequest(
                name="Get",
                method="get",
                url="https://api.example.com/CON",
                folder="CON",
            ),
        ),
    )
    features = build_features(collection)  # type: ignore[arg-type]
    assert "CON_" in features
    assert "CON" not in features
