"""Template set discovery for behave-gen.

A :class:`TemplateSet` wraps a directory of template files and renders them
into a destination directory, preserving the relative directory structure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from behave_gen.templates.engine import TemplateEngine, TemplateRenderError


@dataclass(frozen=True, slots=True)
class TemplateFile:
    """A single template file within a :class:`TemplateSet`."""

    relative_path: Path
    source: Path


@dataclass(frozen=True, slots=True)
class TemplateSet:
    """A directory of templates rendered as a unit."""

    name: str
    root: Path
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
            files.append(
                TemplateFile(relative_path=resolved.relative_to(root_path), source=resolved)
            )
        return cls(name=name or root_path.name, root=root_path, files=tuple(files))

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
            try:
                engine.render_file(template_file.source, target, context)
            except TemplateRenderError:
                raise
            except OSError as exc:
                raise TemplateRenderError(f"Failed to write {target}: {exc}") from exc
            written.append(target)
        return written
