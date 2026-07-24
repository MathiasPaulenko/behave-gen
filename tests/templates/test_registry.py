"""Tests for the template registry."""

from __future__ import annotations

from pathlib import Path

import pytest

from behave_gen.templates.discovery import TemplateSet
from behave_gen.templates.registry import TemplateRegistry, default_registry


def test_registry_register_and_get(tmp_path: Path) -> None:
    registry = TemplateRegistry()
    (tmp_path / "file.txt").write_text("hello", encoding="utf-8")
    ts = TemplateSet.from_directory(tmp_path, name="demo")
    registry.register(ts)
    assert registry.has("demo")
    assert registry.get("demo") is ts
    assert registry.names() == ("demo",)


def test_registry_register_directory(tmp_path: Path) -> None:
    registry = TemplateRegistry()
    (tmp_path / "readme.md").write_text("# demo", encoding="utf-8")
    ts = registry.register_directory(tmp_path, name="custom")
    assert ts.name == "custom"
    assert registry.has("custom")


def test_registry_get_unknown_raises() -> None:
    registry = TemplateRegistry()
    with pytest.raises(KeyError, match="Unknown template set"):
        registry.get("missing")


def test_default_registry_contains_default() -> None:
    registry = default_registry()
    assert registry.has("default")
    ts = registry.get("default")
    assert ts.name == "default"
