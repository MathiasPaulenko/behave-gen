"""``behave-gen add environment`` and ``add config`` commands.

``add environment`` rewrites a project's ``environment.py`` with behave-kit
and/or behave-data wiring. ``add config`` adds an ecosystem package to the
project's ``pyproject.toml`` dependencies idempotently.
"""

from __future__ import annotations

import re
import string
import sys
import tomllib
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

from behave_gen.config import BehaveGenConfig
from behave_gen.paths import resolve_project_root, safe_write_text
from behave_gen.project import Project, ProjectError
from behave_gen.templates.variants import environment_variant

_TEMPLATE_ROOT = "behave_gen.templates.default"

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


def _load_environment_template(variant: str) -> str:
    with resources.as_file(resources.files(_TEMPLATE_ROOT).joinpath(variant)) as p:
        path = Path(p)
        if not path.is_file():
            raise EnvironmentError(f"Environment template not found: {variant}.")
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            raise EnvironmentError(f"Could not read template {variant}: {exc}") from exc
        except UnicodeDecodeError as exc:
            raise EnvironmentError(f"Could not decode template {variant}: {exc}") from exc


def _project_name(root: Path) -> str:
    """Read ``project.name`` from ``pyproject.toml`` or fall back to directory name."""
    pyproject = root / "pyproject.toml"
    if not pyproject.is_file():
        return root.name
    try:
        text = pyproject.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return root.name
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return root.name
    name = data.get("project", {}).get("name")
    if isinstance(name, str) and name:
        return name
    return root.name


def add_environment(
    project_root: str | Path,
    options: AddEnvironmentOptions,
    *,
    environment_file: str | Path = "environment.py",
) -> Path:
    """Rewrite ``environment.py`` with the requested kit/data wiring.

    Args:
        project_root: Root of the Behave project.
        options: Add-environment options.
        environment_file: Path to the environment file, relative to the project
            root or absolute.

    Returns:
        The path to the written ``environment.py``.

    Raises:
        EnvironmentError: If the project root is missing or the file cannot be
            written.
    """
    root = Path(project_root).resolve()
    if not root.is_dir():
        raise EnvironmentError(f"Project root not found: {root}")

    variant = environment_variant(options.kit, options.data)
    raw = _load_environment_template(variant)

    project_name = _project_name(root)
    try:
        rendered = string.Template(raw).substitute(
            project_name=project_name.replace("\\", "\\\\").replace('"', '\\"'),
        )
    except KeyError as exc:
        key = exc.args[0] if exc.args else "<unknown>"
        raise EnvironmentError(f"Missing template variable ${key}.") from exc

    target = Path(environment_file)
    if not target.is_absolute():
        target = root / environment_file
    target = target.resolve()
    if not target.is_relative_to(root):
        raise EnvironmentError(f"Environment file {target} must be inside project root {root}.")
    if target.is_dir() and not target.is_symlink():
        raise EnvironmentError(f"Cannot overwrite directory: {target}")
    try:
        if target.exists() or target.is_symlink():
            target.unlink()
    except OSError as exc:
        raise EnvironmentError(f"Could not remove existing file {target}: {exc}") from exc

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise EnvironmentError(f"Could not create parent directory {target.parent}: {exc}") from exc

    try:
        safe_write_text(target, rendered)
    except OSError as exc:
        raise EnvironmentError(f"Could not write environment file {target}: {exc}") from exc
    return target


def run_add_environment(
    options: AddEnvironmentOptions,
    project_root: str | Path | None = None,
    *,
    config: BehaveGenConfig | None = None,
) -> int:
    """CLI entry point for ``behave-gen add environment``."""
    root = resolve_project_root(project_root)
    try:
        project = Project.from_root(root, config=config)
    except ProjectError as exc:
        print(f"add environment: {exc}", file=sys.stderr)
        return 1
    try:
        path = add_environment(project.root, options, environment_file=project.environment_file)
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


def add_config(
    project_root: str | Path,
    name: str,
    *,
    pyproject: str | Path | None = None,
) -> Path:
    """Add an ecosystem package to the project's ``pyproject.toml``.

    Args:
        project_root: Root of the Behave project.
        name: Config name (``behave-kit`` or ``behave-data``).
        pyproject: Optional explicit ``pyproject.toml`` path. Defaults to
            ``<project_root>/pyproject.toml``.

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

    package_spec, extra = _CONFIG_PACKAGES[name]
    config_path = Path(pyproject) if pyproject is not None else root / "pyproject.toml"
    config_path = config_path.resolve()
    if not config_path.is_relative_to(root):
        raise EnvironmentError(
            f"pyproject.toml path {config_path} must be inside project root {root}."
        )
    if not config_path.is_file():
        raise EnvironmentError(f"pyproject.toml not found in {root}.")

    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise EnvironmentError(f"Could not read {config_path}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise EnvironmentError(f"Could not decode {config_path}: {exc}") from exc

    try:
        new_text = _insert_optional_dependency(text, package_spec, extra)
    except (ValueError, IndexError) as exc:
        raise EnvironmentError(f"Could not update {config_path}: {exc}") from exc

    if new_text == text and package_spec not in text:
        raise EnvironmentError(f"Could not insert {package_spec!r} into {config_path}.")

    try:
        safe_write_text(config_path, new_text)
    except OSError as exc:
        raise EnvironmentError(f"Could not write {config_path}: {exc}") from exc
    return config_path


def _find_section(lines: list[str], header: str, start: int = 0) -> int | None:
    """Return the index of a TOML table header, or None."""
    for i in range(start, len(lines)):
        if lines[i].strip() == header:
            return i
    return None


def _insert_optional_dependency(  # noqa: PLR0912 - TOML tree walk is inherently branchy.
    text: str,
    package_spec: str,
    extra: str,
) -> str:
    """Insert ``package_spec`` into the matching optional-dependencies extra.

    If the section or extra does not exist, it is created. Returns the updated
    text, or the original text if the dependency is already present.
    """
    lines = text.splitlines(keepends=True)
    opt_idx = _find_section(lines, "[project.optional-dependencies]")
    if opt_idx is None:
        return _create_optional_section(lines, extra, package_spec)

    extra_header = f"{extra} = ["
    section_end: int | None = None
    for i in range(opt_idx + 1, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith("[") and stripped != "[project.optional-dependencies]":
            section_end = i
            break
    end_idx = section_end if section_end is not None else len(lines)

    extra_idx: int | None = None
    for i in range(opt_idx + 1, end_idx):
        if lines[i].strip().startswith(extra_header):
            extra_idx = i
            break

    if extra_idx is None:
        block = [f"{extra} = [\n", f'    "{package_spec}",\n', "]\n"]
        if section_end is not None and lines[section_end - 1].strip() != "":
            block.insert(0, "\n")
            # Adjust insertion point so the blank line sits before the next table.
            insert_at = section_end
        else:
            insert_at = end_idx
        lines[insert_at:insert_at] = block
        return "".join(lines)

    close_idx: int | None = None
    for j in range(extra_idx + 1, end_idx):
        if lines[j].strip() == "]":
            close_idx = j
            break
    if close_idx is None:
        # Malformed array; append at the end of the section as a best effort.
        lines.insert(end_idx, f'    "{package_spec}",\n')
        return "".join(lines)

    existing_pattern = re.compile(rf'^\s*"{re.escape(package_spec)}"\s*,?\s*$')
    for j in range(extra_idx + 1, close_idx):
        if existing_pattern.search(lines[j]):
            return text

    lines.insert(close_idx, f'    "{package_spec}",\n')
    return "".join(lines)


def _create_optional_section(lines: list[str], extra: str, package_spec: str) -> str:
    """Create ``[project.optional-dependencies]`` and the requested extra."""
    block = [
        "\n",
        "[project.optional-dependencies]\n",
        f"{extra} = [\n",
        f'    "{package_spec}",\n',
        "]\n",
    ]
    urls_idx = _find_section(lines, "[project.urls]")
    if urls_idx is not None:
        lines[urls_idx:urls_idx] = block
    else:
        if lines and not lines[-1].endswith("\n"):
            lines.append("\n")
        lines.extend(block)
    return "".join(lines)


def run_add_config(
    name: str,
    project_root: str | Path | None = None,
    *,
    config: BehaveGenConfig | None = None,
) -> int:
    """CLI entry point for ``behave-gen add config``."""
    root = resolve_project_root(project_root)
    try:
        project = Project.from_root(root, config=config)
    except ProjectError as exc:
        print(f"add config: {exc}", file=sys.stderr)
        return 1
    try:
        path = add_config(project.root, name, pyproject=project.root / "pyproject.toml")
    except EnvironmentError as exc:
        print(f"add config: {exc}", file=sys.stderr)
        return 1
    print(f"Updated {path} with {name}.")
    return 0
