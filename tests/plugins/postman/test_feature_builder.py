"""Tests for the Postman feature builder."""

from __future__ import annotations

from pathlib import Path

from behave_model import parse_feature

from behave_gen.plugins.postman import build_features
from behave_gen.plugins.postman.parser import parse_postman

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


def test_build_features_uses_http_step_syntax() -> None:
    features = build_features(_collection())  # type: ignore[arg-type]
    content = features["Auth"]
    assert 'When I send a POST request to "/auth/login"' in content
    assert "Then the response status should be 200" in content
