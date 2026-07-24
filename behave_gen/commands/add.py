"""``behave-gen add`` command implementations.

Phase 5 implements ``add feature``. Other ``add`` subcommands are wired in
later phases.
"""

from __future__ import annotations

import string
import sys
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

from behave_model import ParseError, parse_feature

_FEATURE_TEMPLATE_ROOT = "behave_gen.templates.features"


class AddError(Exception):
    """User-facing error raised by add commands."""


def _normalize_tags(tags: str | None) -> str:
    """Normalize a tag string into a ``@tag1 @tag2\\n`` prefix line.

    Accepts comma- or space-separated tags. Returns an empty string when no
    tags are provided, so the template collapses to ``Feature: ...``.
    """
    if not tags:
        return ""
    cleaned = tags.replace(",", " ")
    parts = [p for p in cleaned.split() if p]
    if not parts:
        return ""
    normalized = [p if p.startswith("@") else f"@{p}" for p in parts]
    return " ".join(normalized) + "\n"


def _feature_template_path(template: str) -> Path:
    """Return the on-disk path to a feature template."""
    with resources.as_file(
        resources.files(_FEATURE_TEMPLATE_ROOT).joinpath(f"{template}.feature")
    ) as p:
        path = Path(p)
    if not path.is_file():
        raise AddError(
            f"Unknown feature template {template!r}. Available templates: default, crud."
        )
    return path


@dataclass(frozen=True, slots=True)
class AddFeatureOptions:
    """Options for ``add feature``."""

    name: str
    tags: str | None = None
    template: str = "default"


def _humanize(name: str) -> str:
    """Turn a slug like ``user_login`` into ``User login``."""
    return name.replace("_", " ").replace("-", " ").capitalize()


def add_feature(
    project_root: str | Path,
    options: AddFeatureOptions,
    *,
    features_dir: str = "features",
) -> Path:
    """Generate a ``.feature`` file inside ``project_root``.

    Args:
        project_root: Root of the Behave project.
        options: Add-feature options.
        features_dir: Features directory relative to ``project_root``.

    Returns:
        The path to the generated feature file.

    Raises:
        AddError: If the project/features dir is missing, the template is
            unknown, the name is invalid, or the generated file fails to parse.
    """
    name = options.name.strip()
    if not name or any(ch in name for ch in ("\\", ":", "*", "?", '"', "<", ">", "|", "/")):
        raise AddError(f"Invalid feature name: {name!r}.")

    root = Path(project_root).resolve()
    if not root.is_dir():
        raise AddError(f"Project root not found: {root}")

    features = root / features_dir
    features.mkdir(parents=True, exist_ok=True)
    target = features / f"{name}.feature"
    if target.exists():
        raise AddError(f"Feature file already exists: {target}. Use a different name or remove it.")

    template_path = _feature_template_path(options.template)
    raw = template_path.read_text(encoding="utf-8")
    context = {
        "feature_name": _humanize(name),
        "name": name,
        "tags": _normalize_tags(options.tags),
    }
    try:
        rendered = string.Template(raw).substitute(context)
    except KeyError as exc:
        raise AddError(f"Missing template variable ${exc.args[0]}.") from exc

    # Validate the generated feature parses cleanly with behave-model.
    try:
        parse_feature(rendered, filename=str(target))
    except ParseError as exc:
        raise AddError(f"Generated feature failed to parse: {exc}") from exc

    target.write_text(rendered, encoding="utf-8")
    return target


def run_add_feature(
    options: AddFeatureOptions,
    project_root: str | Path | None = None,
) -> int:
    """CLI entry point for ``behave-gen add feature``."""
    root = Path(project_root) if project_root is not None else Path.cwd()
    try:
        path = add_feature(root, options)
    except AddError as exc:
        print(f"add feature: {exc}", file=sys.stderr)
        return 1
    print(f"Created feature at {path}")
    return 0
