"""Feature builder for the OpenAPI plugin.

Turns an :class:`OpenApiSpec` into Gherkin ``.feature`` file contents, grouped
by path. Each path becomes one feature file with one scenario per HTTP method.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from behave_gen.plugins.openapi.parser import OpenApiOperation, OpenApiSpec


def _safe_filename(path: str) -> str:
    """Convert an OpenAPI path into a filesystem-safe feature name."""
    cleaned = path.strip("/").replace("/", "_").replace("{", "").replace("}", "")
    cleaned = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in cleaned)
    return cleaned or "root"


def _humanize(path: str) -> str:
    """Turn ``/users/{id}`` into ``Users by id``."""
    parts = [p for p in path.strip("/").split("/") if p]
    human: list[str] = []
    for part in parts:
        if part.startswith("{") and part.endswith("}"):
            human.append(f"by {part[1:-1]}")
        else:
            human.append(part.replace("_", " ").replace("-", " ").capitalize())
    return " ".join(human) or "Root"


def _scenario_for(operation: OpenApiOperation, tag: str | None) -> str:
    """Build a single scenario block for an operation."""
    method = operation.method.upper()
    title = operation.summary or f"{method} {operation.path}"
    lines = [
        f"  Scenario: {title}",
        f'    When I send a {method} request to "{operation.path}"',
        "    Then the response status should be 200",
    ]
    if tag:
        lines.insert(0, f"  @{tag}")
    return "\n".join(lines)


def build_feature_text(
    path: str,
    operations: list[OpenApiOperation],
    *,
    title: str,
    tag: str | None = None,
) -> str:
    """Build the full ``.feature`` file text for a single path."""
    header_tags = f"@{tag}\n" if tag else ""
    feature_name = _humanize(path)
    description = f"Scenarios for {feature_name} generated from {title}."
    scenarios = "\n\n".join(_scenario_for(op, tag=None) for op in operations)
    return f"{header_tags}Feature: {feature_name}\n  {description}\n\n{scenarios}\n"


def build_features(
    spec: OpenApiSpec,
    *,
    tag: str | None = None,
    include_paths: list[str] | None = None,
    include_methods: list[str] | None = None,
) -> dict[str, str]:
    """Build feature file contents grouped by path.

    Args:
        spec: Parsed OpenAPI spec.
        tag: Optional tag added to every feature and scenario.
        include_paths: Optional path allow-list (exact match).
        include_methods: Optional method allow-list (lowercase).

    Returns:
        Mapping of filename (without extension) -> feature file text.
    """
    path_ops: dict[str, list[OpenApiOperation]] = defaultdict(list)
    path_filter = set(include_paths) if include_paths else None
    method_filter = {m.lower() for m in include_methods} if include_methods else None

    for op in spec.operations:
        if path_filter is not None and op.path not in path_filter:
            continue
        if method_filter is not None and op.method not in method_filter:
            continue
        path_ops[op.path].append(op)

    result: dict[str, str] = {}
    for path, ops in path_ops.items():
        filename = _safe_filename(path)
        result[filename] = build_feature_text(path, ops, title=spec.title, tag=tag)
    return result


def _filter_kwargs(options: dict[str, Any]) -> dict[str, Any]:
    """Extract the filter kwargs accepted by :func:`build_features`."""
    return {
        "tag": options.get("tag"),
        "include_paths": options.get("include_paths"),
        "include_methods": options.get("include_methods"),
    }
