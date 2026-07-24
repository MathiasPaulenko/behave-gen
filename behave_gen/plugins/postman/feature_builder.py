"""Feature builder for the Postman plugin.

Turns a :class:`PostmanCollection` into Gherkin ``.feature`` file contents,
grouped by Postman folder. Each request becomes one scenario using the HTTP
step library syntax.
"""

from __future__ import annotations

from collections import defaultdict

from behave_gen.plugins.postman.parser import PostmanCollection, PostmanRequest, url_to_path


def _safe_filename(folder: str) -> str:
    """Convert a folder name into a filesystem-safe feature name."""
    cleaned = folder.replace("/", "_").replace("\\", "_").replace(" ", "_")
    cleaned = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in cleaned)
    return cleaned or "root"


def _humanize(folder: str) -> str:
    """Turn ``Auth/Login`` into ``Auth Login``."""
    return folder.replace("/", " ").replace("_", " ").strip() or "Root"


def _scenario_for(request: PostmanRequest) -> str:
    """Build a single scenario block for a Postman request."""
    method = request.method.upper()
    path = url_to_path(request.url)
    title = request.name or f"{method} {path}"
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
    tag: str | None = None,
) -> str:
    """Build the full ``.feature`` file text for a single folder."""
    header_tags = f"@{tag}\n" if tag else ""
    feature_name = _humanize(folder) if folder else title
    description = f"Scenarios for {feature_name} generated from {title}."
    scenarios = "\n\n".join(_scenario_for(req) for req in requests)
    return f"{header_tags}Feature: {feature_name}\n  {description}\n\n{scenarios}\n"


def build_features(
    collection: PostmanCollection,
    *,
    tag: str | None = None,
) -> dict[str, str]:
    """Build feature file contents grouped by Postman folder.

    Args:
        collection: Parsed Postman collection.
        tag: Optional tag added to every feature.

    Returns:
        Mapping of filename (without extension) -> feature file text.
    """
    folder_reqs: dict[str, list[PostmanRequest]] = defaultdict(list)
    for req in collection.requests:
        folder_reqs[req.folder].append(req)

    result: dict[str, str] = {}
    for folder, reqs in folder_reqs.items():
        filename = _safe_filename(folder) if folder else _safe_filename(collection.name)
        result[filename] = build_feature_text(folder, reqs, title=collection.name, tag=tag)
    return result
