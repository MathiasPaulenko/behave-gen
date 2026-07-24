"""``behave-gen add steps`` command implementation.

Copies a built-in step library (a real, runnable step-definition module) into
a project's ``features/steps/`` directory. No empty ``pass`` skeletons are
ever emitted (see ``ref/adr/0001-no-empty-step-skeletons.md``).
"""

from __future__ import annotations

import string
import sys
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

_STEP_LIB_ROOT = "behave_gen.step_libraries"

# Built-in libraries: name -> (template filename, output filename).
_BUILTIN_LIBRARIES: dict[str, tuple[str, str]] = {
    "http": ("http_steps.py.tpl", "http_steps.py"),
    "auth": ("auth_steps.py.tpl", "auth_steps.py"),
}


class AddStepsError(Exception):
    """User-facing error raised by ``add steps``."""


@dataclass(frozen=True, slots=True)
class AddStepsOptions:
    """Options for ``add steps``."""

    lib: str
    from_openapi: str | None = None


def _template_path(template_name: str) -> Path:
    with resources.as_file(resources.files(_STEP_LIB_ROOT).joinpath(template_name)) as p:
        path = Path(p)
    if not path.is_file():
        raise AddStepsError(f"Step library template not found: {template_name}.")
    return path


def _available_libraries() -> tuple[str, ...]:
    return tuple(sorted(_BUILTIN_LIBRARIES))


def add_steps(
    project_root: str | Path,
    options: AddStepsOptions,
    *,
    steps_dir: str = "features/steps",
) -> Path:
    """Copy a step library into ``project_root``'s steps directory.

    Args:
        project_root: Root of the Behave project.
        options: Add-steps options.
        steps_dir: Steps directory relative to ``project_root``.

    Returns:
        The path to the written step-definition file.

    Raises:
        AddStepsError: If the project is missing, the library is unknown, or
            the file already exists.
    """
    if options.lib not in _BUILTIN_LIBRARIES:
        available = ", ".join(_available_libraries())
        raise AddStepsError(f"Unknown step library {options.lib!r}. Available: {available}.")

    root = Path(project_root).resolve()
    if not root.is_dir():
        raise AddStepsError(f"Project root not found: {root}")

    steps = root / steps_dir
    steps.mkdir(parents=True, exist_ok=True)

    template_name, output_name = _BUILTIN_LIBRARIES[options.lib]
    target = steps / output_name
    if target.exists():
        raise AddStepsError(
            f"Step file already exists: {target}. Remove it or choose another library."
        )

    template_path = _template_path(template_name)
    raw = template_path.read_text(encoding="utf-8")
    project_name = root.name
    try:
        rendered = string.Template(raw).substitute(project_name=project_name)
    except KeyError as exc:
        raise AddStepsError(f"Missing template variable ${exc.args[0]}.") from exc

    target.write_text(rendered, encoding="utf-8")
    return target


def run_add_steps(
    options: AddStepsOptions,
    project_root: str | Path | None = None,
) -> int:
    """CLI entry point for ``behave-gen add steps``."""
    root = Path(project_root) if project_root is not None else Path.cwd()
    try:
        path = add_steps(root, options)
    except AddStepsError as exc:
        print(f"add steps: {exc}", file=sys.stderr)
        return 1
    print(f"Added step library {options.lib!r} at {path}")
    return 0
