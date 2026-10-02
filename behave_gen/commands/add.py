"""``behave-gen add feature`` command implementation."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

from behave_model import ParseError, parse_feature

from behave_gen.config import BehaveGenConfig
from behave_gen.paths import (
    resolve_project_root,
    safe_parse_feature_filename,
    safe_write_text,
    validate_name,
)
from behave_gen.project import Project, ProjectError
from behave_gen.templates.engine import TemplateRenderError, get_engine

_FEATURE_TEMPLATE_ROOT = "behave_gen.templates.features"


class AddError(Exception):
    """User-facing error raised by add commands."""


def _tag_parts(tags: str | None) -> tuple[str, ...]:
    """Split a user tag string into individual tag parts."""
    if not tags:
        return ()
    cleaned = tags.replace(",", " ")
    return tuple(p for p in cleaned.split() if p)


def _format_tag_line(parts: tuple[str, ...]) -> str:
    r"""Render tag parts as a ``@tag1 @tag2\n`` prefix line.

    Returns an empty string when no tags are provided, so the template
    collapses to ``Feature: ...``.
    """
    if not parts:
        return ""
    normalized = sorted({p if p.startswith("@") else f"@{p}" for p in parts})
    return " ".join(normalized) + "\n"


def _load_feature_template(template: str, templates_dir: Path | None = None) -> str:
    """Return the source text for a feature template.

    Custom ``<name>.feature`` files under ``templates_dir`` take precedence
    over the built-in templates shipped with behave-gen.
    """
    if templates_dir is not None:
        base = Path(templates_dir).resolve()
        candidate = (base / f"{template}.feature").resolve()
        if not candidate.is_relative_to(base):
            raise AddError(f"Feature template {template!r} escapes the templates directory {base}.")
        if candidate.is_file():
            try:
                return candidate.read_text(encoding="utf-8")
            except OSError as exc:
                raise AddError(f"Could not read template {template}: {exc}") from exc
            except UnicodeDecodeError as exc:
                raise AddError(f"Could not decode template {template}: {exc}") from exc

    with resources.as_file(
        resources.files(_FEATURE_TEMPLATE_ROOT).joinpath(f"{template}.feature")
    ) as p:
        path = Path(p)
        if not path.is_file():
            raise AddError(
                f"Unknown feature template {template!r}. Available built-ins: default, crud."
            )
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            raise AddError(f"Could not read template {template}: {exc}") from exc
        except UnicodeDecodeError as exc:
            raise AddError(f"Could not decode template {template}: {exc}") from exc


@dataclass(frozen=True, slots=True)
class AddFeatureOptions:
    """Options for ``add feature``."""

    name: str
    tags: str | None = None
    template: str = "default"


def _humanize(name: str) -> str:
    """Turn a slug like ``user_login`` into ``User Login``."""
    spaced = name.replace("_", " ").replace("-", " ").replace("#", " ")
    return re.sub(r"\b\w", lambda match: match.group(0).upper(), spaced)


def add_feature(  # noqa: PLR0913 - keyword-only knobs mirror the project config.
    project_root: str | Path,
    options: AddFeatureOptions,
    *,
    features_dir: str | Path = "features",
    default_tags: tuple[str, ...] = (),
    templates_dir: str | Path | None = None,
    template_engine: str = "string",
) -> Path:
    """Generate a ``.feature`` file inside ``project_root``.

    Args:
        project_root: Root of the Behave project.
        options: Add-feature options.
        features_dir: Features directory relative to ``project_root``.
        default_tags: Default tags from project configuration, merged with
            tags supplied on ``options``.
        templates_dir: Directory with custom ``.feature`` templates that take
            precedence over the built-in ones.
        template_engine: Template engine used to render the template
            (``string`` or ``jinja2``).

    Returns:
        The path to the generated feature file.

    Raises:
        AddError: If the project/features dir is missing, the template is
            unknown, the name is invalid, or the generated file fails to parse.

    """
    try:
        name = validate_name(options.name)
    except ValueError as exc:
        raise AddError(f"Invalid feature name: {exc}") from exc

    root = Path(project_root).resolve()
    if not root.is_dir():
        raise AddError(f"Project root not found: {root}")

    features = (root / features_dir).resolve()
    if not features.is_relative_to(root):
        raise AddError(f"Features directory {features} escapes project root {root}.")
    try:
        features.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise AddError(f"Could not create features directory {features}: {exc}") from exc
    target = features / f"{name}.feature"
    if not target.is_relative_to(features):
        raise AddError(f"Feature file {target} must be inside features directory {features}.")
    if target.exists() or target.is_symlink():
        raise AddError(f"Feature file already exists: {target}. Use a different name or remove it.")

    raw = _load_feature_template(
        options.template, Path(templates_dir) if templates_dir is not None else None
    )
    all_tags = default_tags + _tag_parts(options.tags)
    context = {
        "feature_name": _humanize(name),
        "name": name,
        "tags": _format_tag_line(all_tags),
    }
    try:
        rendered = get_engine(template_engine).render(
            raw, context, filename=f"{options.template}.feature"
        )
    except (TemplateRenderError, ValueError) as exc:
        raise AddError(str(exc)) from exc

    # Validate the generated feature parses cleanly with behave-model.
    try:
        parse_feature(rendered, filename=safe_parse_feature_filename(target))
    except ParseError as exc:
        raise AddError(f"Generated feature failed to parse: {exc}") from exc

    try:
        safe_write_text(target, rendered)
    except OSError as exc:
        raise AddError(f"Could not write feature file {target}: {exc}") from exc
    return target


def run_add_feature(
    options: AddFeatureOptions,
    project_root: str | Path | None = None,
    *,
    config: BehaveGenConfig | None = None,
) -> int:
    """CLI entry point for ``behave-gen add feature``."""
    root = resolve_project_root(project_root)
    try:
        project = Project.from_root(root, config=config)
    except ProjectError as exc:
        print(f"add feature: {exc}", file=sys.stderr)
        return 1
    try:
        path = add_feature(
            project.root,
            options,
            features_dir=project.features_dir,
            default_tags=project.config.default_tags,
            templates_dir=project.templates_dir,
            template_engine=project.config.template_engine,
        )
    except AddError as exc:
        print(f"add feature: {exc}", file=sys.stderr)
        return 1
    print(f"Created feature at {path}")
    return 0
