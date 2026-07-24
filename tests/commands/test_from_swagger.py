"""Tests for ``behave-gen from-swagger`` command security/validation."""

from __future__ import annotations

import shutil
from pathlib import Path

from behave_gen.commands.from_swagger import FromSwaggerOptions, run_from_swagger
from behave_gen.commands.init import InitOptions, init_project

_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "swagger"


def _make_project(tmp_path: Path) -> Path:
    return init_project(tmp_path, InitOptions(name="proj"))


def test_from_swagger_rejects_relative_spec_outside_project_root(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    spec = _FIXTURES / "petstore_swagger2.json"
    shutil.copy(spec, root / "petstore_swagger2.json")
    rc = run_from_swagger(
        FromSwaggerOptions(spec="../petstore_swagger2.json", out_dir="gen"),
        project_root=root,
    )
    assert rc == 1


def test_from_swagger_accepts_relative_spec_inside_project_root(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    spec = _FIXTURES / "petstore_swagger2.json"
    shutil.copy(spec, root / "petstore_swagger2.json")
    rc = run_from_swagger(
        FromSwaggerOptions(spec="petstore_swagger2.json", out_dir="gen"),
        project_root=root,
    )
    assert rc == 0
    assert (root / "gen" / "features").is_dir()


def test_from_swagger_accepts_absolute_spec(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    spec = _FIXTURES / "petstore_swagger2.json"
    rc = run_from_swagger(
        FromSwaggerOptions(spec=str(spec), out_dir="gen"),
        project_root=root,
    )
    assert rc == 0
