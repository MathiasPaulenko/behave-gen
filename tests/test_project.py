"""Tests for behave_gen.project and behave_gen.paths."""

from __future__ import annotations

from pathlib import Path

import pytest

from behave_gen.config import BehaveGenConfig
from behave_gen.paths import relative_to, resolve_path
from behave_gen.project import Project, ProjectError, discover_project, find_project_root


def test_resolve_path_relative_uses_cwd() -> None:
    resolved = resolve_path("foo")
    assert resolved.is_absolute()


def test_resolve_path_with_base(tmp_path: Path) -> None:
    resolved = resolve_path("bar", tmp_path)
    assert resolved == (tmp_path / "bar").resolve()


def test_relative_to_inside_base(tmp_path: Path) -> None:
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    assert relative_to(nested, tmp_path) == Path("a") / "b"


def test_relative_to_outside_base_raises(tmp_path: Path) -> None:
    other = tmp_path.parent
    with pytest.raises(ValueError):
        relative_to(tmp_path, other / "nonexistent-sibling")


def test_find_project_root_locates_marker(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
    nested = tmp_path / "src" / "deep"
    nested.mkdir(parents=True)
    assert find_project_root(nested) == tmp_path.resolve()


def test_find_project_root_with_behave_toml(tmp_path: Path) -> None:
    (tmp_path / "behave.toml").write_text("[behave]\n", encoding="utf-8")
    assert find_project_root(tmp_path) == tmp_path.resolve()


def test_find_project_root_no_marker_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="No project marker"):
        find_project_root(tmp_path)


def test_project_from_root_resolves_paths(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.behave-gen]\nfeatures_dir = "specs"\n', encoding="utf-8"
    )
    project = Project.from_root(tmp_path)
    assert project.root == tmp_path.resolve()
    assert project.features_dir == (tmp_path / "specs").resolve()
    assert project.config_file == (tmp_path / "behave.toml").resolve()
    assert isinstance(project.config, BehaveGenConfig)


def test_project_from_root_with_explicit_config(tmp_path: Path) -> None:
    config = BehaveGenConfig.default().with_overrides(features_dir="custom")
    project = Project.from_root(tmp_path, config=config)
    assert project.features_dir == (tmp_path / "custom").resolve()
    assert project.config is config


def test_discover_project_from_nested_dir(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
    nested = tmp_path / "features" / "steps"
    nested.mkdir(parents=True)
    project = discover_project(nested)
    assert project.root == tmp_path.resolve()


def test_project_is_frozen(tmp_path: Path) -> None:
    project = Project.from_root(tmp_path)
    with pytest.raises(AttributeError):
        project.root = tmp_path / "other"  # type: ignore[misc]


def test_project_from_root_rejects_escaping_config_paths(tmp_path: Path) -> None:
    config = BehaveGenConfig.default().with_overrides(features_dir="../outside")
    with pytest.raises(ProjectError, match="escapes project root"):
        Project.from_root(tmp_path, config=config)
