"""``behave-gen add environment`` and ``add config`` commands.

``add environment`` rewrites a project's ``environment.py`` with behave-kit
and/or behave-data wiring. ``add config`` adds an ecosystem package to the
project's ``pyproject.toml`` dependencies idempotently.
"""

from __future__ import annotations

import string
import sys
import tomllib
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

_TEMPLATE_ROOT = "behave_gen.templates.default"

_ENVIRONMENT_VARIANTS = {
    (False, False): "environment.py",
    (True, False): "environment_with_kit.py",
    (False, True): "environment_with_data.py",
    (True, True): "environment_with_kit_data.py",
}

# Maps config name -> (package spec, extra group).
_CONFIG_PACKAGES: dict[str, tuple[str, str]] = {
    "behave-kit": ("behave-kit>=1.0", "kit"),
    "behave-data": ("behave-data>=1.0", "data"),
}


class EnvironmentError(Exception):
    """User-facing error raised by environment/config commands."""


@dataclass(frozen=True, slots=True)
class AddEnvironmentOptions:
    """Options for ``add environment``."""

    kit: bool = False
    data: bool = False


def _variant_template_path(variant: str) -> Path:
    with resources.as_file(resources.files(_TEMPLATE_ROOT).joinpath(variant)) as p:
        path = Path(p)
    if not path.is_file():
        raise EnvironmentError(f"Environment template not found: {variant}.")
    return path


def _project_name(root: Path) -> str:
    pyproject = root / "pyproject.toml"
    if not pyproject.is_file():
        return root.name
    with pyproject.open("rb") as handle:
        data = tomllib.load(handle)
    name = data.get("project", {}).get("name")
    if isinstance(name, str) and name:
        return name
    return root.name


def add_environment(
    project_root: str | Path,
    options: AddEnvironmentOptions,
) -> Path:
    """Rewrite ``environment.py`` with the requested kit/data wiring.

    Args:
        project_root: Root of the Behave project.
        options: Add-environment options.

    Returns:
        The path to the written ``environment.py``.

    Raises:
        EnvironmentError: If the project root is missing.
    """
    root = Path(project_root).resolve()
    if not root.is_dir():
        raise EnvironmentError(f"Project root not found: {root}")

    variant = _ENVIRONMENT_VARIANTS[(options.kit, options.data)]
    template_path = _variant_template_path(variant)
    raw = template_path.read_text(encoding="utf-8")
    project_name = _project_name(root)
    try:
        rendered = string.Template(raw).substitute(project_name=project_name)
    except KeyError as exc:
        raise EnvironmentError(f"Missing template variable ${exc.args[0]}.") from exc

    target = root / "environment.py"
    target.write_text(rendered, encoding="utf-8")
    return target


def run_add_environment(
    options: AddEnvironmentOptions,
    project_root: str | Path | None = None,
) -> int:
    """CLI entry point for ``behave-gen add environment``."""
    root = Path(project_root) if project_root is not None else Path.cwd()
    try:
        path = add_environment(root, options)
    except EnvironmentError as exc:
        print(f"add environment: {exc}", file=sys.stderr)
        return 1
    flags = []
    if options.kit:
        flags.append("kit")
    if options.data:
        flags.append("data")
    label = " + ".join(flags) if flags else "base"
    print(f"Updated environment.py ({label}) at {path}")
    return 0


def add_config(project_root: str | Path, name: str) -> Path:
    """Add an ecosystem package to the project's ``pyproject.toml``.

    Args:
        project_root: Root of the Behave project.
        name: Config name (``behave-kit`` or ``behave-data``).

    Returns:
        The path to the updated ``pyproject.toml``.

    Raises:
        EnvironmentError: If the project root or pyproject.toml is missing, or
            the config name is unknown.
    """
    root = Path(project_root).resolve()
    if not root.is_dir():
        raise EnvironmentError(f"Project root not found: {root}")

    if name not in _CONFIG_PACKAGES:
        available = ", ".join(sorted(_CONFIG_PACKAGES))
        raise EnvironmentError(f"Unknown config {name!r}. Available: {available}.")

    pyproject = root / "pyproject.toml"
    if not pyproject.is_file():
        raise EnvironmentError(f"pyproject.toml not found in {root}.")

    package_spec, extra = _CONFIG_PACKAGES[name]
    text = pyproject.read_text(encoding="utf-8")

    if package_spec in text:
        # Idempotent: already present.
        return pyproject

    new_text = _insert_dependency(text, package_spec, extra)
    if new_text == text:
        # Fallback: append to a [project] dependencies block if present.
        new_text = _append_dependency(text, package_spec)
    pyproject.write_text(new_text, encoding="utf-8")
    return pyproject


def _insert_dependency(text: str, package_spec: str, extra: str) -> str:
    """Insert ``package_spec`` into the matching optional-dependencies extra.

    If the extra does not exist, it is created. Returns the updated text, or
    the original text if no insertion point was found.
    """
    lines = text.splitlines(keepends=True)
    # Find [project.optional-dependencies] section.
    try:
        opt_idx = next(
            i for i, line in enumerate(lines) if line.strip() == "[project.optional-dependencies]"
        )
    except StopIteration:
        # No optional-dependencies section; create one before [project.urls] or end.
        return _create_optional_section(lines, extra, package_spec)

    # Find the extra subsection within optional-dependencies.
    extra_header = f"{extra} = ["
    for i in range(opt_idx + 1, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith("[") and stripped != "[project.optional-dependencies]":
            # Reached next table; insert the extra before it.
            block = [
                f"{extra} = [\n",
                f'    "{package_spec}",\n',
                "]\n",
                "\n",
            ]
            lines[i:i] = block
            return "".join(lines)
        if stripped.startswith(extra_header):
            # Extra exists; insert package_spec if not already present.
            if package_spec in "".join(lines[i : i + 4]):
                return text
            insert_at = i + 1
            # Skip to first content line.
            while insert_at < len(lines) and '"]' not in lines[insert_at - 1]:
                if package_spec in lines[insert_at]:
                    return text
                if lines[insert_at].strip() == "]":
                    break
                insert_at += 1
            lines.insert(insert_at, f'    "{package_spec}",\n')
            return "".join(lines)
    # Append extra at end of optional-dependencies.
    lines.append(f"{extra} = [\n")
    lines.append(f'    "{package_spec}",\n')
    lines.append("]\n")
    return "".join(lines)


def _create_optional_section(lines: list[str], extra: str, package_spec: str) -> str:
    block = [
        "\n",
        "[project.optional-dependencies]\n",
        f"{extra} = [\n",
        f'    "{package_spec}",\n',
        "]\n",
    ]
    # Insert before [project.urls] if present, else append.
    for i, line in enumerate(lines):
        if line.strip() == "[project.urls]":
            lines[i:i] = block
            return "".join(lines)
    lines.extend(block)
    return "".join(lines)


def _append_dependency(text: str, package_spec: str) -> str:
    """Fallback: append the package to the main dependencies list."""
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.strip() == "dependencies = [":
            # Insert before the closing bracket.
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == "]":
                    lines.insert(j, f'    "{package_spec}",\n')
                    return "".join(lines)
    return text


def run_add_config(name: str, project_root: str | Path | None = None) -> int:
    """CLI entry point for ``behave-gen add config``."""
    root = Path(project_root) if project_root is not None else Path.cwd()
    try:
        path = add_config(root, name)
    except EnvironmentError as exc:
        print(f"add config: {exc}", file=sys.stderr)
        return 1
    print(f"Updated {path} with {name}.")
    return 0
