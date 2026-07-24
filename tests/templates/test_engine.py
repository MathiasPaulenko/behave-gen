"""Tests for the template engine, discovery, and registry."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from behave_gen.commands.init import InitOptions, init_project
from behave_gen.templates.discovery import TemplateSet
from behave_gen.templates.engine import (
    TemplateRenderError,
    get_engine,
)
from behave_gen.templates.registry import TemplateRegistry, default_registry

# --- Engine -----------------------------------------------------------------


def test_string_engine_renders_placeholders() -> None:
    engine = get_engine("string")
    assert engine.render("Hello $name", {"name": "world"}) == "Hello world"


def test_string_engine_missing_placeholder_raises_with_filename() -> None:
    engine = get_engine("string")
    with pytest.raises(TemplateRenderError, match="Missing template variable"):
        engine.render("Hello $missing", {}, filename="README.md")


def test_string_engine_missing_placeholder_includes_filename() -> None:
    engine = get_engine("string")
    with pytest.raises(TemplateRenderError, match="README.md"):
        engine.render("$missing", {}, filename="README.md")


def test_get_engine_unknown_raises() -> None:
    with pytest.raises(ValueError, match="Unknown template engine"):
        get_engine("mako")


def test_jinja2_engine_optional() -> None:
    pytest.importorskip("jinja2")
    engine = get_engine("jinja2")
    assert engine.render("Hello {{ name }}", {"name": "world"}) == "Hello world"


def test_jinja2_engine_missing_placeholder_raises() -> None:
    pytest.importorskip("jinja2")
    engine = get_engine("jinja2")
    with pytest.raises(TemplateRenderError, match="jinja2 render error"):
        engine.render("{{ missing }}", {}, filename="x.j2")


# --- Discovery --------------------------------------------------------------


def _make_template_dir(tmp_path: Path) -> Path:
    root = tmp_path / "tpl"
    (root / "sub").mkdir(parents=True)
    (root / "top.txt").write_text("top $name", encoding="utf-8")
    (root / "sub" / "nested.txt").write_text("nested $project_name", encoding="utf-8")
    (root / "static.bin").write_bytes(b"\x00\x01")
    return root


def test_template_set_from_directory(tmp_path: Path) -> None:
    root = _make_template_dir(tmp_path)
    ts = TemplateSet.from_directory(root, name="demo")
    assert ts.name == "demo"
    rels = {f.relative_path.as_posix() for f in ts.files}
    assert "top.txt" in rels
    assert "sub/nested.txt" in rels
    assert "static.bin" in rels


def test_template_set_render_to_preserves_structure(tmp_path: Path) -> None:
    root = _make_template_dir(tmp_path)
    ts = TemplateSet.from_directory(root)
    dest = tmp_path / "out"
    written = ts.render_to(dest, {"name": "x", "project_name": "p"}, get_engine("string"))
    assert (dest / "top.txt").read_text(encoding="utf-8") == "top x"
    assert (dest / "sub" / "nested.txt").read_text(encoding="utf-8") == "nested p"
    assert (dest / "static.bin").read_bytes() == b"\x00\x01"
    assert len(written) == 3


def test_template_set_render_to_skip_and_rename(tmp_path: Path) -> None:
    root = tmp_path / "tpl"
    root.mkdir()
    (root / "environment.py").write_text("base $name", encoding="utf-8")
    (root / "environment_with_kit.py").write_text("kit $name", encoding="utf-8")
    ts = TemplateSet.from_directory(root)
    dest = tmp_path / "out"
    ts.render_to(
        dest,
        {"name": "x"},
        get_engine("string"),
        skip=frozenset({"environment.py"}),
        rename={"environment_with_kit.py": "environment.py"},
    )
    assert (dest / "environment.py").read_text(encoding="utf-8") == "kit x"


def test_template_set_missing_directory_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        TemplateSet.from_directory(tmp_path / "nope")


# --- Registry ---------------------------------------------------------------


def test_default_registry_has_default(tmp_path: Path) -> None:
    reg = default_registry()
    assert reg.has("default")
    ts = reg.get("default")
    assert ts.name == "default"


def test_registry_unknown_raises_with_available() -> None:
    reg = default_registry()
    with pytest.raises(KeyError, match="Unknown template set"):
        reg.get("nope")


def test_registry_register_custom_directory(tmp_path: Path) -> None:
    root = _make_template_dir(tmp_path)
    reg = TemplateRegistry()
    reg.register_directory(root, name="custom")
    assert reg.has("custom")
    assert "custom" in reg.names()


# --- Integration: init still works after refactor --------------------------


def test_init_uses_registry_and_engine(tmp_path: Path) -> None:
    root = init_project(tmp_path, InitOptions(name="proj"))
    assert (root / "environment.py").is_file()
    assert (root / "pyproject.toml").is_file()
    assert "proj" in (root / "README.md").read_text(encoding="utf-8")


def test_init_jinja2_engine_when_installed(tmp_path: Path) -> None:
    pytest.importorskip("jinja2")
    # The default templates use $name placeholders, so jinja2 rendering of
    # $name is a literal pass-through; this just verifies the engine path.
    root = init_project(tmp_path, InitOptions(name="proj", template_engine="jinja2"))
    assert (root / "README.md").is_file()


def test_template_set_ignores_symlinks_outside_root(tmp_path: Path) -> None:
    root = tmp_path / "tpl"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    link = root / "link.txt"
    try:
        os.symlink(outside, link)
    except OSError:
        pytest.skip("Symlinks are not supported in this environment")
    ts = TemplateSet.from_directory(root)
    assert len(ts.files) == 0
