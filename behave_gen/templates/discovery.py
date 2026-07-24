"""Template set discovery for behave-gen.

A :class:`TemplateSet` wraps a directory of template files and renders them
into a destination directory, preserving the relative directory structure.

Templates are loaded into memory when the set is built so that built-in sets
shipped inside zip packages can be rendered without relying on extracted files
remaining on disk.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib.resources.abc import Traversable
from pathlib import Path, PurePath
from typing import Any

from behave_gen.templates.engine import TemplateEngine, TemplateRenderError


@dataclass(frozen=True, slots=True)
class TemplateFile:
    """A single template file within a :class:`TemplateSet`."""

    relative_path: PurePath
    content: str


@dataclass(frozen=True, slots=True)
class TemplateSet:
    """A directory of templates rendered as a unit."""

    name: str
    files: tuple[TemplateFile, ...] = field(default_factory=tuple)

    @classmethod
    def from_directory(cls, root: str | Path, name: str | None = None) -> TemplateSet:
        """Build a :class:`TemplateSet` from a directory on disk.

        Args:
            root: Directory containing template files.
            name: Optional name; defaults to the directory name.
        """
        root_path = Path(root).resolve()
        if not root_path.is_dir():
            raise FileNotFoundError(f"Template set directory not found: {root_path}")
        files = _collect_path_files(root_path)
        return cls(name=name or root_path.name, files=tuple(files))

    @classmethod
    def from_package(cls, root: Traversable, name: str) -> TemplateSet:
        """Build a :class:`TemplateSet` from a package resource tree.

        Works for regular directories and for resources stored inside zip
        wheels, avoiding the need to keep a temporary extracted directory alive.
        """
        if not root.is_dir():
            raise FileNotFoundError(f"Template set directory not found: {root}")
        files = _collect_traversable_files(root)
        return cls(name=name, files=tuple(files))

    def render_to(
        self,
        destination: str | Path,
        context: dict[str, Any],
        engine: TemplateEngine,
        *,
        skip: frozenset[str] | None = None,
        rename: dict[str, str] | None = None,
    ) -> list[Path]:
        """Render every file in the set into ``destination``.

        Args:
            destination: Target directory (created if missing).
            context: Variables passed to the engine.
            engine: Template engine used to render file contents.
            skip: Basenames to skip entirely.
            rename: Mapping of relative path strings to new relative paths,
                used to emit e.g. ``environment_with_kit.py`` as
                ``environment.py``.

        Returns:
            The list of written file paths.
        """
        skip_names = skip or frozenset()
        rename_map = rename or {}
        dest_root = Path(destination).resolve()
        written: list[Path] = []
        for template_file in self.files:
            rel = template_file.relative_path
            if rel.name in skip_names:
                continue
            rel_str = rel.as_posix()
            new_rel: PurePath
            if rel_str in rename_map:
                new_rel = Path(rename_map[rel_str])
            elif rel.name in rename_map:
                new_rel = rel.parent / rename_map[rel.name]
            else:
                new_rel = rel
            if new_rel.is_absolute() or ".." in new_rel.parts:
                raise TemplateRenderError(
                    f"Invalid rename path {new_rel!r}: must be relative and not contain '..'."
                )
            target = dest_root / new_rel
            target.parent.mkdir(parents=True, exist_ok=True)
            rendered = engine.render(
                template_file.content,
                context,
                filename=rel_str,
            )
            target.write_text(rendered, encoding="utf-8")
            written.append(target)
        return written


def _collect_path_files(root_path: Path) -> list[TemplateFile]:
    """Collect all text files under ``root_path`` into :class:`TemplateFile`s."""
    files: list[TemplateFile] = []
    for p in sorted(root_path.rglob("*")):
        if not p.is_file():
            continue
        try:
            resolved = p.resolve()
        except (OSError, RuntimeError):
            continue
        if not resolved.is_relative_to(root_path):
            continue
        try:
            content = resolved.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = resolved.relative_to(root_path)
        files.append(TemplateFile(relative_path=rel, content=content))
    return files


def _collect_traversable_files(
    root: Traversable, prefix: PurePath | None = None
) -> list[TemplateFile]:
    """Recursively collect files from a package resource tree."""
    files: list[TemplateFile] = []
    prefix = prefix or PurePath(".")
    for child in root.iterdir():
        if child.is_dir():
            sub_prefix = prefix / child.name
            files.extend(_collect_traversable_files(child, sub_prefix))
            continue
        if not child.is_file():
            continue
        try:
            content = child.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = prefix / child.name
        files.append(TemplateFile(relative_path=rel, content=content))
    return files
