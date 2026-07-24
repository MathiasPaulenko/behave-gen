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

# environment.py variants selected by the --kit / --data flags.
_ENVIRONMENT_VARIANTS = {
    (False, False): "environment.py",
    (True, False): "environment_with_kit.py",
    (False, True): "environment_with_data.py",
    (True, True): "environment_with_kit_data.py",
}

# All environment variant filenames; only the selected one is emitted.
_ALL_ENVIRONMENT_VARIANTS = frozenset(_ENVIRONMENT_VARIANTS.values())


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


def _environment_variant(kit: bool, data: bool) -> str:
    return _ENVIRONMENT_VARIANTS[(kit, data)]


def _build_skip_and_rename(kit: bool, data: bool) -> tuple[frozenset[str], dict[str, str]]:
    """Compute which environment variants to skip and which to rename."""
    selected = _environment_variant(kit, data)
    skip: set[str] = set()
    rename: dict[str, str] = {}
    for variant in _ALL_ENVIRONMENT_VARIANTS:
        if variant == "environment.py":
            # The base environment.py is only emitted when selected.
            if selected != "environment.py":
                skip.add(variant)
            continue
        if variant == selected:
            rename[variant] = "environment.py"
        else:
            skip.add(variant)
    return frozenset(skip), rename


def init_project(
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
    parent.mkdir(parents=True, exist_ok=True)
    project_root = parent / name

    if project_root.exists():
        if not options.force:
            raise InitError(f"Directory already exists: {project_root}. Use --force to overwrite.")
        shutil.rmtree(project_root)

    project_root.mkdir(parents=True)

    reg = registry if registry is not None else default_registry()
    try:
        template_set = reg.get(options.template)
    except KeyError as exc:
        raise InitError(str(exc)) from exc

    try:
        engine = get_engine(options.template_engine)
    except ValueError as exc:
        raise InitError(str(exc)) from exc

    skip, rename = _build_skip_and_rename(options.kit, options.data)
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
