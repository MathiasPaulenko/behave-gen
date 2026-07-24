"""``behave-gen preview`` command implementation.

Pretty-prints a ``.feature`` file using a lightweight renderer that works with
``behave.model.Feature`` objects returned by ``behave-model``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from behave_model import ParseError, parse_feature

from behave_gen.config import BehaveGenConfig
from behave_gen.paths import resolve_project_root
from behave_gen.project import Project, ProjectError


class PreviewError(Exception):
    """User-facing error raised by ``preview``."""


def _render_tags(tags: Any, indent: str = "") -> list[str]:
    """Render a tag list as a single ``@tag1 @tag2`` line (or empty)."""
    tag_list = list(tags or [])
    if not tag_list:
        return []
    rendered = " ".join(str(t) for t in tag_list)
    return [f"{indent}{rendered}"]


def _render_table(table: Any, indent: str) -> list[str]:
    """Render a behave model table as Gherkin pipe-separated rows."""
    rows = list(getattr(table, "rows", []) or [])
    if not rows:
        return []
    headers = list(getattr(rows[0], "cells", []) or [])
    all_rows = [headers] + [list(getattr(r, "cells", []) or []) for r in rows[1:]]
    widths = [
        max(
            len(str(row[i] if row[i] is not None else "")) if i < len(row) else 0
            for row in all_rows
        )
        for i in range(len(headers))
    ]
    lines: list[str] = []
    for row in all_rows:
        cells = " | ".join(
            str(row[i] if i < len(row) and row[i] is not None else "").ljust(widths[i])
            for i in range(len(widths))
        )
        lines.append(f"{indent}| {cells} |")
    return lines


def _render_step(step: Any, indent: str) -> list[str]:
    """Render a single step."""
    keyword = getattr(step, "keyword", "Given")
    name = getattr(step, "name", "")
    lines = [f"{indent}{keyword} {name}".rstrip()]
    # Doc string
    text = getattr(step, "text", None)
    if isinstance(text, str) and text:
        lines.append(f'{indent}"""')
        for text_line in text.splitlines():
            lines.append(f"{indent}  {text_line}")
        lines.append(f'{indent}"""')
    # Data table
    table = getattr(step, "table", None)
    if table:
        lines.extend(_render_table(table, indent + "  "))
    return lines


def _render_scenario(scenario: Any, indent: str) -> list[str]:
    """Render a scenario (plain or outline)."""
    lines: list[str] = []
    lines.extend(_render_tags(getattr(scenario, "tags", []), indent))
    cls_name = type(scenario).__name__
    keyword = "Scenario Outline" if cls_name == "ScenarioOutline" else "Scenario"
    name = getattr(scenario, "name", "")
    lines.append(f"{indent}{keyword}: {name}")
    step_indent = indent + "  "
    for step in getattr(scenario, "steps", []) or []:
        lines.extend(_render_step(step, step_indent))
    # Examples for outlines
    examples = getattr(scenario, "examples", []) or []
    for example in examples:
        ex_name = getattr(example, "name", "")
        name_part = f" {ex_name}" if ex_name else ""
        lines.append(f"{step_indent}Examples:{name_part}")
        lines.extend(_render_table(getattr(example, "table", None), step_indent + "  "))
    return lines


def render_feature(feature: Any) -> str:
    """Render a ``behave.model.Feature`` as Gherkin text."""
    lines: list[str] = []
    lines.extend(_render_tags(getattr(feature, "tags", [])))
    name = getattr(feature, "name", "")
    lines.append(f"Feature: {name}")
    desc = getattr(feature, "description", None)
    if isinstance(desc, list):
        lines.extend(f"  {line}" for line in desc if line is not None)
    elif isinstance(desc, str) and desc:
        lines.extend(f"  {line}" for line in desc.splitlines())
    # Background
    background = getattr(feature, "background", None)
    if background:
        lines.append(f"  Background: {getattr(background, 'name', '')}".rstrip())
        for step in getattr(background, "steps", []) or []:
            lines.extend(_render_step(step, "    "))
    for scenario in getattr(feature, "scenarios", []) or []:
        lines.append("")
        lines.extend(_render_scenario(scenario, "  "))
    return "\n".join(lines) + "\n"


def _resolve_preview_path(feature_path: str, root: Path) -> tuple[Path | None, str | None]:
    """Resolve and validate a feature path for preview.

    Returns the resolved path and ``None`` on success, or ``None`` and an error
    message on failure.
    """
    path = Path(feature_path)
    if not path.is_absolute():
        path = root / path
    try:
        path = path.resolve()
    except (OSError, RuntimeError) as exc:
        return None, f"Could not resolve feature path {path}: {exc}"
    if not path.is_relative_to(root):
        return None, f"Feature file must be inside project root: {path}"
    if not path.is_file():
        return None, f"Feature file not found: {path}"
    return path, None


def run_preview(
    feature_path: str,
    project_root: str | Path | None = None,
    *,
    config: BehaveGenConfig | None = None,
) -> int:
    """CLI entry point for ``behave-gen preview``."""
    root = resolve_project_root(project_root)
    try:
        project = Project.from_root(root, config=config)
    except ProjectError as exc:
        print(f"preview: {exc}", file=sys.stderr)
        return 1

    path, error = _resolve_preview_path(feature_path, project.root)
    if error is not None:
        print(f"preview: {error}", file=sys.stderr)
        return 1
    if path is None:
        return 1

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        kind = "read" if isinstance(exc, OSError) else "decode as UTF-8"
        print(f"preview: Could not {kind} {path}: {exc}", file=sys.stderr)
        return 1
    try:
        feature = parse_feature(text, filename=str(path))
    except ParseError as exc:
        print(f"preview: Parse error: {exc}", file=sys.stderr)
        return 1

    print(render_feature(feature))
    return 0
