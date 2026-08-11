"""Tests for ``behave-gen add feature``."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from behave_model import parse_feature
from typer.testing import CliRunner

from behave_gen.cli.app import app
from behave_gen.commands.add import AddError, AddFeatureOptions, add_feature
from behave_gen.commands.init import InitOptions, init_project
from behave_gen.paths import safe_parse_feature_filename

runner = CliRunner()


def _make_project(tmp_path: Path) -> Path:
    return init_project(tmp_path, InitOptions(name="proj"))


def test_add_feature_creates_file(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    path = add_feature(root, AddFeatureOptions(name="login"))
    assert path == (root / "features" / "login.feature").resolve()
    assert path.is_file()
    content = path.read_text(encoding="utf-8")
    assert "Feature: Login" in content
    assert "Scenario: Login scenario" in content


def test_add_feature_humanizes_multi_word_slug(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    path = add_feature(root, AddFeatureOptions(name="user_login"))
    content = path.read_text(encoding="utf-8")
    assert "Feature: User Login" in content


def test_add_feature_parses_with_behave_model(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    path = add_feature(root, AddFeatureOptions(name="checkout"))
    feature = parse_feature(
        path.read_text(encoding="utf-8"), filename=safe_parse_feature_filename(path)
    )
    assert feature.name == "Checkout"


def test_add_feature_with_tags(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    path = add_feature(root, AddFeatureOptions(name="auth", tags="@smoke @api"))
    content = path.read_text(encoding="utf-8")
    assert content.startswith("@smoke @api\nFeature:")


def test_add_feature_tags_comma_separated(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    path = add_feature(root, AddFeatureOptions(name="auth", tags="smoke, api"))
    content = path.read_text(encoding="utf-8")
    assert content.startswith("@smoke @api\nFeature:")


def test_add_feature_tags_without_at_prefix(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    path = add_feature(root, AddFeatureOptions(name="auth", tags="smoke"))
    assert path.read_text(encoding="utf-8").startswith("@smoke\nFeature:")


def test_add_feature_crud_template(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    path = add_feature(root, AddFeatureOptions(name="user", template="crud"))
    content = path.read_text(encoding="utf-8")
    assert "Scenario Outline:" in content
    assert "Examples:" in content
    assert "Background:" in content


def test_add_feature_existing_file_raises(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    add_feature(root, AddFeatureOptions(name="login"))
    with pytest.raises(AddError, match="already exists"):
        add_feature(root, AddFeatureOptions(name="login"))


def test_add_feature_existing_symlink_raises(tmp_path: Path) -> None:
    """A pre-existing symlink must be treated as an existing file."""
    root = _make_project(tmp_path)
    outside = tmp_path / "outside.feature"
    outside.write_text("Feature: Outside\n", encoding="utf-8")
    link = root / "features" / "login.feature"
    try:
        os.symlink(outside, link)
    except OSError:
        pytest.skip("Symlinks are not supported in this environment")
    with pytest.raises(AddError, match="already exists"):
        add_feature(root, AddFeatureOptions(name="login"))


def test_add_feature_invalid_name_raises(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    with pytest.raises(AddError, match="Invalid feature name"):
        add_feature(root, AddFeatureOptions(name="bad/name"))


def test_add_feature_unknown_template_raises(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    with pytest.raises(AddError, match="Unknown feature template"):
        add_feature(root, AddFeatureOptions(name="x", template="nope"))


def test_add_feature_missing_project_root_raises(tmp_path: Path) -> None:
    with pytest.raises(AddError, match="Project root not found"):
        add_feature(tmp_path / "nope", AddFeatureOptions(name="x"))


def test_add_feature_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path)
    monkeypatch.chdir(root)
    result = runner.invoke(app, ["add", "feature", "signup"])
    assert result.exit_code == 0, result.output
    assert (root / "features" / "signup.feature").is_file()


def test_add_feature_cli_existing_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path)
    monkeypatch.chdir(root)
    runner.invoke(app, ["add", "feature", "dup"], catch_exceptions=False)
    result = runner.invoke(app, ["add", "feature", "dup"])
    assert result.exit_code == 1
    assert "already exists" in result.output


def test_add_feature_rejects_dot_names(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    for name in (".", ".."):
        with pytest.raises(AddError, match="Invalid feature name"):
            add_feature(root, AddFeatureOptions(name=name))


def test_add_feature_rejects_path_traversal(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    with pytest.raises(AddError, match="Invalid feature name"):
        add_feature(root, AddFeatureOptions(name="../escape"))


def test_add_feature_rejects_features_dir_outside_root(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    with pytest.raises(AddError, match="escapes project root"):
        add_feature(root, AddFeatureOptions(name="login"), features_dir="../escape")


def test_generated_feature_behave_dry_run(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    add_feature(root, AddFeatureOptions(name="login"))
    proc = subprocess.run(
        [sys.executable, "-m", "behave", "--dry-run", "--no-color"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    # Undefined steps are expected (no step library added yet), but there must
    # be no syntax/parse errors. behave reports undefined steps as errors, so
    # we only assert the feature was parsed (no ConfigError/ParseError).
    assert "ConfigError" not in proc.stdout
    assert "ParseError" not in proc.stdout
    assert "Feature: Login" in proc.stdout
