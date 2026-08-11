"""Postman Collection v2.1 parser.

Loads a Postman Collection JSON file and exposes a small, typed model
(:class:`PostmanCollection`, :class:`PostmanRequest`) that the feature builder
consumes. Only the v2.1 schema is supported; v1 collections are rejected with
a clear error.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

# Reject collections larger than 10 MiB before reading them into memory.
_MAX_COLLECTION_SIZE_BYTES = 10 * 1024 * 1024


class PostmanParseError(Exception):
    """Raised when a Postman collection cannot be parsed."""


@dataclass(frozen=True, slots=True)
class PostmanRequest:
    """A single request extracted from a Postman collection."""

    name: str
    method: str
    url: str
    folder: str


@dataclass(frozen=True, slots=True)
class PostmanCollection:
    """A typed view of a Postman Collection v2.1."""

    name: str
    schema: str
    requests: tuple[PostmanRequest, ...] = field(default_factory=tuple)


def _stringify_url_part(part: Any) -> str | None:
    """Render a Postman URL host/path segment to a string, handling variables."""
    if part is None:
        return None
    if isinstance(part, str):
        return part
    if isinstance(part, dict):
        value = part.get("value")
        if isinstance(value, str):
            return value
        key = part.get("key")
        if isinstance(key, str):
            return key
    return str(part)


def _resolve_url(url_field: Any) -> str:
    """Resolve a Postman URL field (string or object) to a plain URL string."""
    if url_field is None:
        return ""
    if isinstance(url_field, str):
        return url_field
    if isinstance(url_field, dict):
        raw = url_field.get("raw")
        if isinstance(raw, str):
            return raw
        host = url_field.get("host")
        path = url_field.get("path", [])
        if isinstance(host, list):
            host_str = ".".join(p for p in (_stringify_url_part(p) for p in host) if p is not None)
        elif isinstance(host, str):
            host_str = host
        else:
            host_str = ""
        if isinstance(path, list):
            path_str = "/".join(p for p in (_stringify_url_part(p) for p in path) if p is not None)
        else:
            path_str = str(path)
        if host_str:
            protocol = url_field.get("protocol")
            if isinstance(protocol, str) and protocol:
                host_str = f"{protocol}://{host_str}"
            else:
                # Without a scheme urlparse cannot extract the netloc, so use a safe default.
                host_str = f"http://{host_str}"
        return f"{host_str}/{path_str}".rstrip("/")
    return str(url_field)


def _extract_requests(items: list[Any], parent_folder: str = "") -> list[PostmanRequest]:
    """Recursively extract requests from Postman items, tracking folder names."""
    requests: list[PostmanRequest] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "Unnamed")
        if "item" in item and isinstance(item["item"], list):
            folder = name if not parent_folder else f"{parent_folder}/{name}"
            requests.extend(_extract_requests(item["item"], folder))
            continue
        request = item.get("request")
        if not isinstance(request, dict):
            continue
        method_raw = request.get("method", "GET")
        if isinstance(method_raw, str) and method_raw.strip():
            method = method_raw.strip().lower()
        else:
            method = "get"
        url = _resolve_url(request.get("url"))
        requests.append(PostmanRequest(name=name, method=method, url=url, folder=parent_folder))
    return requests


def parse_postman(source: str | Path) -> PostmanCollection:
    """Parse a Postman Collection v2.1 JSON file.

    Raises:
        PostmanParseError: If the file is missing, not valid JSON, or not a
            Postman v2.1 collection.

    """
    path = Path(source)
    if not path.is_file():
        raise PostmanParseError(f"Postman collection not found: {path}")

    try:
        size = path.stat().st_size
    except OSError as exc:
        raise PostmanParseError(f"Could not inspect {path}: {exc}") from exc
    if size > _MAX_COLLECTION_SIZE_BYTES:
        raise PostmanParseError(
            f"Collection too large: {path} ({size} bytes). "
            f"Max allowed: {_MAX_COLLECTION_SIZE_BYTES}."
        )

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PostmanParseError(f"Could not read {path}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise PostmanParseError(f"Could not decode {path} as UTF-8: {exc}") from exc
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        raise PostmanParseError(f"Invalid JSON: {exc}") from exc

    if not isinstance(doc, dict):
        raise PostmanParseError("Top-level JSON value must be an object.")

    info = doc.get("info", {})
    if not isinstance(info, dict):
        raise PostmanParseError("'info' must be a mapping.")

    schema = str(info.get("schema") or "")
    if "v2.1" not in schema and "v2.0" not in schema:
        raise PostmanParseError(
            f"Unsupported Postman schema {schema!r}. Only v2.0/v2.1 are supported."
        )

    items = doc.get("item", [])
    if not isinstance(items, list):
        raise PostmanParseError("'item' must be a list.")

    requests = _extract_requests(items)
    return PostmanCollection(
        name=str(info.get("name") or "Postman Collection"),
        schema=schema,
        requests=tuple(requests),
    )


def url_to_path(url: str) -> str:
    """Convert a full URL into a path component for HTTP step syntax."""
    parsed = urlparse(url)
    if parsed.path:
        return parsed.path
    return "/"
