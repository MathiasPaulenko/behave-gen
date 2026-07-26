"""``behave-gen init`` command implementation.

Scaffolds a new Behave project from a built-in template set using the
pluggable template engine (:mod:`behave_gen.templates`).
"""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from behave_gen.paths import resolve_project_root, validate_name
from behave_gen.templates.engine import TemplateRenderError, get_engine
from behave_gen.templates.registry import TemplateRegistry, default_registry
from behave_gen.templates.variants import build_skip_and_rename


class InitError(Exception):
    """User-facing error raised by the init command."""


@dataclass(frozen=True, slots=True)
class InitOptions:
    """Options for the init command."""

    name: str
    template: str = "default"
    kit: bool = False
    data: bool = False
    force: bool = False
    template_engine: str = "string"


def init_project(  # noqa: PLR0912 - force overwrite has many filesystem-state branches.
    target_dir: str | Path,
    options: InitOptions,
    registry: TemplateRegistry | None = None,
) -> Path:
    """Create a new Behave project at ``target_dir/options.name``.

    Args:
        target_dir: Parent directory where the project folder is created.
        options: Init options.
        registry: Optional template registry; defaults to the built-in one.

    Returns:
        The resolved path to the created project root.

    Raises:
        InitError: If the target exists and ``force`` is not set, the template
            is unknown, the project name is invalid, or rendering fails.

    """
    try:
        name = validate_name(options.name)
    except ValueError as exc:
        raise InitError(f"Invalid project name: {exc}") from exc

    parent = Path(target_dir).resolve()
    if parent.exists() and not parent.is_dir():
        raise InitError(f"Target path exists but is not a directory: {parent}")
    try:
        parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise InitError(f"Could not create target directory {parent}: {exc}") from exc

    project_root = parent / name

    if project_root.exists() or project_root.is_symlink():
        if not options.force:
            raise InitError(f"Directory already exists: {project_root}. Use --force to overwrite.")
        try:
            if project_root.is_symlink():
                if project_root.is_dir() and sys.platform == "win32":
                    project_root.rmdir()
                else:
                    project_root.unlink()
            elif project_root.is_file():
                project_root.unlink()
            else:
                shutil.rmtree(project_root)
        except OSError as exc:
            raise InitError(f"Could not remove existing project {project_root}: {exc}") from exc

    try:
        project_root.mkdir(parents=True)
    except OSError as exc:
        raise InitError(f"Could not create project directory {project_root}: {exc}") from exc

    reg = registry if registry is not None else default_registry()
    try:
        template_set = reg.get(options.template)
    except KeyError as exc:
        raise InitError(str(exc)) from exc

    try:
        engine = get_engine(options.template_engine)
    except ValueError as exc:
        raise InitError(str(exc)) from exc

    skip, rename = build_skip_and_rename(options.kit, options.data)
    context = {"project_name": name, "name": name}
    try:
        template_set.render_to(project_root, context, engine, skip=skip, rename=rename)
    except TemplateRenderError as exc:
        raise InitError(str(exc)) from exc
    return project_root


def run_init(options: InitOptions, target_dir: str | Path | None = None) -> int:
    """CLI entry point for ``behave-gen init``."""
    parent = resolve_project_root(target_dir)
    try:
        root = init_project(parent, options)
    except InitError as exc:
        print(f"init: {exc}", file=sys.stderr)
        return 1
    print(f"Created Behave project at {root}")
    return 0
