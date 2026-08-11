"""Tests for the Cucumber migrator."""

from __future__ import annotations

from pathlib import Path

import pytest
from behave_model import parse_feature

from behave_gen.paths import safe_parse_feature_filename
from behave_gen.plugins.cucumber.migrator import (
    MigrationError,
    migrate_cucumber,
)

FIXTURES = Path(__file__).resolve().parent.parent.parent / "fixtures" / "cucumber"


def test_migrate_copies_feature_files(tmp_path: Path) -> None:
    out = tmp_path / "out"
    report = migrate_cucumber(FIXTURES, out)
    assert len(report.features) == 2
    assert (
        out / "features" / "src" / "test" / "resources" / "features" / "login.feature"
    ).is_file()
    assert (
        out / "features" / "src" / "test" / "resources" / "features" / "checkout.feature"
    ).is_file()


def test_migrate_strips_language_directive(tmp_path: Path) -> None:
    out = tmp_path / "out"
    migrate_cucumber(FIXTURES, out)
    content = (
        out / "features" / "src" / "test" / "resources" / "features" / "login.feature"
    ).read_text(encoding="utf-8")
    assert "# language:" not in content
    assert "Feature: Login" in content


def test_migrate_warns_about_java_steps(tmp_path: Path) -> None:
    out = tmp_path / "out"
    report = migrate_cucumber(FIXTURES, out)
    assert any("Java step definition" in w for w in report.warnings)


def test_migrate_generated_features_parse(tmp_path: Path) -> None:
    out = tmp_path / "out"
    report = migrate_cucumber(FIXTURES, out)
    for feature_file in report.features:
        parse_feature(
            feature_file.read_text(encoding="utf-8"),
            filename=safe_parse_feature_filename(feature_file),
        )


def test_migrate_missing_source_raises(tmp_path: Path) -> None:
    with pytest.raises(MigrationError, match="Source not found"):
        migrate_cucumber(tmp_path / "nope", tmp_path / "out")


def test_migrate_no_features_raises(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(MigrationError, match="No .feature files"):
        migrate_cucumber(empty, tmp_path / "out")


def test_migrate_single_feature_file(tmp_path: Path) -> None:
    out = tmp_path / "out"
    single = FIXTURES / "src" / "test" / "resources" / "features" / "login.feature"
    report = migrate_cucumber(single, out)
    assert len(report.features) == 1
    assert (out / "features" / "login.feature").is_file()
