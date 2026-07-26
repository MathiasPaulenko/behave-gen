"""Tests for template set discovery."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from behave_gen.templates.discovery import (
    _collect_path_files,
    _collect_traversable_files,
)


def test_collect_path_files_skips_unreadable_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A file that raises OSError while reading must not abort discovery."""
    (tmp_path / "good.txt").write_text("hello", encoding="utf-8")
    (tmp_path / "bad.txt").write_text("secret", encoding="utf-8")

    original = Path.read_text

    def _read_text(self: Path, *args: Any, **kwargs: Any) -> str:
        if self.name == "bad.txt":
            raise OSError("permission denied")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", _read_text)
    files = _collect_path_files(tmp_path)
    assert [f.relative_path.name for f in files] == ["good.txt"]


class _FakeTraversable:
    """Minimal stand-in for ``importlib.resources.abc.Traversable``."""

    def __init__(
        self,
        name: str,
        *,
        content: str = "",
        children: list[_FakeTraversable] | None = None,
        is_dir: bool = False,
    ) -> None:
        self.name = name
        self._content = content
        self._children = children or []
        self._is_dir = is_dir

    def iterdir(self) -> Any:
        return iter(self._children)

    def is_dir(self) -> bool:
        return self._is_dir

    def is_file(self) -> bool:
        return not self._is_dir

    def read_text(self, encoding: str = "utf-8") -> str:  # noqa: ARG002
        if self.name == "bad.txt":
            raise OSError("permission denied")
        return self._content


def test_collect_traversable_files_skips_unreadable_file() -> None:
    """A resource that raises OSError while reading must not abort discovery."""
    root = _FakeTraversable(
        "root",
        is_dir=True,
        children=[
            _FakeTraversable("good.txt", content="hello"),
            _FakeTraversable("bad.txt", content="secret"),
        ],
    )
    files = _collect_traversable_files(root)
    assert [f.relative_path.name for f in files] == ["good.txt"]
