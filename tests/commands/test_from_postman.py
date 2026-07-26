"""Tests for ``behave-gen from-postman`` command security/validation."""

from __future__ import annotations

import shutil
from pathlib import Path

from behave_gen.commands.from_postman import FromPostmanOptions, run_from_postman
from behave_gen.commands.init import InitOptions, init_project

_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "postman"


def _make_project(tmp_path: Path) -> Path:
    return init_project(tmp_path, InitOptions(name="proj"))


def test_from_postman_rejects_relative_collection_outside_project_root(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    collection = _FIXTURES / "sample_collection.json"
    shutil.copy(collection, root / "sample_collection.json")
    rc = run_from_postman(
        FromPostmanOptions(collection="../sample_collection.json", out_dir="gen"),
        project_root=root,
    )
    assert rc == 1


def test_from_postman_accepts_relative_collection_inside_project_root(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    collection = _FIXTURES / "sample_collection.json"
    shutil.copy(collection, root / "sample_collection.json")
    rc = run_from_postman(
        FromPostmanOptions(collection="sample_collection.json", out_dir="gen"),
        project_root=root,
    )
    assert rc == 0
    assert (root / "gen" / "features").is_dir()


def test_from_postman_accepts_absolute_collection(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    collection = _FIXTURES / "sample_collection.json"
    rc = run_from_postman(
        FromPostmanOptions(collection=str(collection), out_dir="gen"),
        project_root=root,
    )
    assert rc == 0


def test_from_postman_resolves_absolute_out_dir_with_dotdot(tmp_path: Path) -> None:
    """An absolute out_dir with parent-directory components must be normalized."""
    root = _make_project(tmp_path)
    collection = _FIXTURES / "sample_collection.json"
    out_dir = str(root / "gen" / ".." / "gen")
    rc = run_from_postman(
        FromPostmanOptions(collection=str(collection), out_dir=out_dir),
        project_root=root,
    )
    assert rc == 0
    assert (root / "gen" / "features").is_dir()
