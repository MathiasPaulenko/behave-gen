"""Feature builder for the OpenAPI plugin.

Turns an :class:`OpenApiSpec` into Gherkin ``.feature`` file contents, grouped
by path. Each path becomes one feature file with one scenario per HTTP method.
"""

from __future__ import annotations

from collections import defaultdict

from behave_gen.plugins.openapi.parser import OpenApiOperation, OpenApiSpec

# Avoid exceeding common filesystem filename limits while leaving room for the
# ``.feature`` extension and any suffix added by callers.
_MAX_FEATURE_FILENAME_LEN = 200


def _safe_filename(path: str) -> str:
    """Convert an OpenAPI path into a filesystem-safe feature name."""
    cleaned = path.strip("/").replace("/", "_").replace("{", "").replace("}", "")
    cleaned = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in cleaned)
    cleaned = cleaned or "root"
    if len(cleaned) > _MAX_FEATURE_FILENAME_LEN:
        cleaned = cleaned[:_MAX_FEATURE_FILENAME_LEN]
    return cleaned


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


def _format_header_tags(tags: tuple[str, ...]) -> str:
    """Render tag parts as a ``@tag1 @tag2\\n`` prefix line."""
    if not tags:
        return ""
    normalized = [t if t.startswith("@") else f"@{t}" for t in tags]
    return " ".join(normalized) + "\n"


def _collect_tags(tag: str | None, default_tags: tuple[str, ...]) -> tuple[str, ...]:
    """Merge an optional tag string with configured default tags."""
    parts: list[str] = []
    parts.extend(default_tags)
    if tag:
        parts.extend(tag.split())
    return tuple(parts)


def _scenario_for(operation: OpenApiOperation) -> str:
    """Build a single scenario block for an operation."""
    method = operation.method.upper()
    title = operation.summary or f"{method} {operation.path}"
    lines = [
        f"  Scenario: {title}",
        f'    When I send a {method} request to "{operation.path}"',
        "    Then the response status should be 200",
    ]
    return "\n".join(lines)


def build_feature_text(
    path: str,
    operations: list[OpenApiOperation],
    *,
    title: str,
    tags: tuple[str, ...] = (),
) -> str:
    """Build the full ``.feature`` file text for a single path."""
    header_tags = _format_header_tags(tags)
    feature_name = _humanize(path)
    description = f"Scenarios for {feature_name} generated from {title}."
    scenarios = "\n\n".join(_scenario_for(op) for op in operations)
    return f"{header_tags}Feature: {feature_name}\n  {description}\n\n{scenarios}\n"


def build_features(
    spec: OpenApiSpec,
    *,
    tag: str | None = None,
    default_tags: tuple[str, ...] = (),
    include_paths: list[str] | None = None,
    include_methods: list[str] | None = None,
) -> dict[str, str]:
    """Build feature file contents grouped by path.

    Args:
        spec: Parsed OpenAPI spec.
        tag: Optional tag added to every generated feature.
        default_tags: Default tags from project configuration, merged with ``tag``.
        include_paths: Optional path allow-list (exact match).
        include_methods: Optional method allow-list (lowercase).

    Returns:
        Mapping of filename (without extension) -> feature file text.
    """
    path_ops: dict[str, list[OpenApiOperation]] = defaultdict(list)
    path_filter = set(include_paths) if include_paths else None
    method_filter = {m.lower() for m in include_methods} if include_methods else None
    merged_tags = _collect_tags(tag, default_tags)

    for op in spec.operations:
        if path_filter is not None and op.path not in path_filter:
            continue
        if method_filter is not None and op.method not in method_filter:
            continue
        path_ops[op.path].append(op)

    result: dict[str, str] = {}
    for path, ops in path_ops.items():
        filename = _safe_filename(path)
        result[filename] = build_feature_text(path, ops, title=spec.title, tags=merged_tags)
    return result
