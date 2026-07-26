"""Tests for ``behave-gen from-openapi`` command security/validation."""

from __future__ import annotations

import shutil
from pathlib import Path

from behave_gen.commands.from_openapi import FromOpenApiOptions, run_from_openapi
from behave_gen.commands.init import InitOptions, init_project

_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "openapi"


def _make_project(tmp_path: Path) -> Path:
    return init_project(tmp_path, InitOptions(name="proj"))


def test_from_openapi_rejects_relative_spec_outside_project_root(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    spec = _FIXTURES / "petstore.json"
    shutil.copy(spec, root / "petstore.json")
    rc = run_from_openapi(
        FromOpenApiOptions(spec="../petstore.json", out_dir="gen"),
        project_root=root,
    )
    assert rc == 1


def test_from_openapi_accepts_relative_spec_inside_project_root(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    spec = _FIXTURES / "petstore.json"
    shutil.copy(spec, root / "petstore.json")
    rc = run_from_openapi(
        FromOpenApiOptions(spec="petstore.json", out_dir="gen"),
        project_root=root,
    )
    assert rc == 0
    assert (root / "gen" / "features").is_dir()


def test_from_openapi_accepts_absolute_spec(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    spec = _FIXTURES / "petstore.json"
    rc = run_from_openapi(
        FromOpenApiOptions(spec=str(spec), out_dir="gen"),
        project_root=root,
    )
    assert rc == 0


def test_from_openapi_resolves_absolute_out_dir_with_dotdot(tmp_path: Path) -> None:
    """An absolute out_dir with parent-directory components must be normalized."""
    root = _make_project(tmp_path)
    spec = _FIXTURES / "petstore.json"
    out_dir = str(root / "gen" / ".." / "gen")
    rc = run_from_openapi(
        FromOpenApiOptions(spec=str(spec), out_dir=out_dir),
        project_root=root,
    )
    assert rc == 0
    assert (root / "gen" / "features").is_dir()
