"""Feature builder for the Postman plugin.

Turns a :class:`PostmanCollection` into Gherkin ``.feature`` file contents,
grouped by Postman folder. Each request becomes one scenario using the HTTP
step library syntax.
"""

from __future__ import annotations

import re
from collections import defaultdict

from behave_gen.paths import is_windows_reserved_name
from behave_gen.plugins.postman.parser import PostmanCollection, PostmanRequest, url_to_path

_MAX_FEATURE_FILENAME_LEN = 200


def _safe_filename(folder: str) -> str:
    """Convert a folder name into a filesystem-safe feature name."""
    cleaned = folder.replace("/", "_").replace("\\", "_").replace(" ", "_")
    cleaned = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in cleaned)
    cleaned = cleaned or "root"
    if is_windows_reserved_name(cleaned):
        cleaned += "_"
    if len(cleaned) > _MAX_FEATURE_FILENAME_LEN:
        cleaned = cleaned[:_MAX_FEATURE_FILENAME_LEN]
    return cleaned


def _unique_filename(base: str, existing: set[str]) -> str:
    """Return a filename that is not already in ``existing``.

    If ``base`` is taken, appends ``_2``, ``_3``, ... while respecting the
    maximum filename length.
    """
    if base not in existing:
        return base
    counter = 2
    while True:
        suffix = f"_{counter}"
        candidate = f"{base[: _MAX_FEATURE_FILENAME_LEN - len(suffix)]}{suffix}"
        if candidate not in existing:
            return candidate
        counter += 1


def _clean_text(value: str) -> str:
    """Collapse all whitespace (including newlines) to single spaces and strip."""
    return " ".join(value.split())


def _format_header_tags(tags: tuple[str, ...]) -> str:
    r"""Render tag parts as a ``@tag1 @tag2\n`` prefix line."""
    if not tags:
        return ""
    normalized = [t if t.startswith("@") else f"@{t}" for t in tags]
    return " ".join(normalized) + "\n"


def _collect_tags(tag: str | None, default_tags: tuple[str, ...]) -> tuple[str, ...]:
    """Merge an optional tag string with configured default tags."""
    parts: list[str] = []
    parts.extend(default_tags)
    if tag:
        parts.extend(tag.replace(",", " ").split())
    return tuple(parts)


def _humanize(folder: str) -> str:
    """Turn ``Auth/Login`` into ``Auth Login``."""
    spaced = folder.replace("/", " ").replace("\\", " ").replace("_", " ").replace("-", " ")
    return _clean_text(re.sub(r"\b\w", lambda match: match.group(0).upper(), spaced)) or "Root"


def _scenario_for(request: PostmanRequest) -> str:
    """Build a single scenario block for a Postman request."""
    method = request.method.upper()
    path = url_to_path(request.url)
    title = _clean_text(request.name or f"{method} {path}")
    lines = [
        f"  Scenario: {title}",
        f'    When I send a {method} request to "{path}"',
        "    Then the response status should be 200",
    ]
    return "\n".join(lines)


def build_feature_text(
    folder: str,
    requests: list[PostmanRequest],
    *,
    title: str,
    tags: tuple[str, ...] = (),
) -> str:
    """Build the full ``.feature`` file text for a single folder."""
    header_tags = _format_header_tags(tags)
    feature_name = _humanize(folder) if folder else title
    description = f"Scenarios for {feature_name} generated from {title}."
    scenarios = "\n\n".join(_scenario_for(req) for req in requests)
    return f"{header_tags}Feature: {feature_name}\n  {description}\n\n{scenarios}\n"


def build_features(
    collection: PostmanCollection,
    *,
    tag: str | None = None,
    default_tags: tuple[str, ...] = (),
) -> dict[str, str]:
    """Build feature file contents grouped by Postman folder.

    Args:
        collection: Parsed Postman collection.
        tag: Optional tag added to every feature.
        default_tags: Default tags from project configuration, merged with ``tag``.

    Returns:
        Mapping of filename (without extension) -> feature file text.

    """
    folder_reqs: dict[str, list[PostmanRequest]] = defaultdict(list)
    for req in collection.requests:
        folder_reqs[req.folder].append(req)

    merged_tags = _collect_tags(tag, default_tags)
    result: dict[str, str] = {}
    used: set[str] = set()
    for folder, reqs in folder_reqs.items():
        base = _safe_filename(folder) if folder else _safe_filename(collection.name)
        filename = _unique_filename(base, used)
        used.add(filename)
        result[filename] = build_feature_text(folder, reqs, title=collection.name, tags=merged_tags)
    return result
