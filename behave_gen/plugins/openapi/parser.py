"""OpenAPI 3.x parser.

Loads an OpenAPI document (YAML or JSON) and exposes a small, typed model
(:class:`OpenApiSpec`, :class:`OpenApiOperation`) that the feature and step
builders consume.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class OpenApiParseError(Exception):
    """Raised when an OpenAPI document cannot be parsed."""


@dataclass(frozen=True, slots=True)
class OpenApiOperation:
    """A single HTTP operation on a path."""

    path: str
    method: str
    operation_id: str
    summary: str
    tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class OpenApiSpec:
    """A minimal, typed view of an OpenAPI 3.x document."""

    title: str
    version: str
    openapi_version: str
    operations: tuple[OpenApiOperation, ...] = field(default_factory=tuple)


def _load_document(source: Path) -> dict[str, Any]:
    text = source.read_text(encoding="utf-8")
    suffix = source.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        try:
            import yaml  # noqa: PLC0415 - optional extra.
        except ImportError as exc:
            raise OpenApiParseError(
                "YAML support requires the 'openapi' extra. "
                "Install it with: pip install behave-gen[openapi]"
            ) from exc
        loaded = yaml.safe_load(text)
    elif suffix == ".json":
        loaded = json.loads(text)
    else:
        # Try JSON first, then YAML.
        try:
            loaded = json.loads(text)
        except json.JSONDecodeError:
            try:
                import yaml  # noqa: PLC0415 - optional extra.
            except ImportError as exc:
                raise OpenApiParseError("YAML support requires the 'openapi' extra.") from exc
            loaded = yaml.safe_load(text)
    if not isinstance(loaded, dict):
        raise OpenApiParseError(
            f"Expected a mapping at the top level, got {type(loaded).__name__}."
        )
    return loaded


def _operation_id(op: dict[str, Any], method: str, path: str) -> str:
    oid = op.get("operationId")
    if isinstance(oid, str) and oid:
        return oid
    cleaned = path.strip("/").replace("/", "_").replace("{", "").replace("}", "")
    return f"{method}_{cleaned}" or method


def _summary(op: dict[str, Any]) -> str:
    summary = op.get("summary")
    if isinstance(summary, str) and summary:
        return summary
    desc = op.get("description")
    if isinstance(desc, str) and desc:
        return desc.splitlines()[0]
    return ""


def _tags(op: dict[str, Any]) -> tuple[str, ...]:
    raw = op.get("tags", [])
    if not isinstance(raw, list):
        return ()
    return tuple(str(tag) for tag in raw if isinstance(tag, str) and tag)


def parse_openapi(source: str | Path) -> OpenApiSpec:
    """Parse an OpenAPI 3.x document into an :class:`OpenApiSpec`.

    Raises:
        OpenApiParseError: If the document is missing, unreadable, or not a
            valid OpenAPI 3.x mapping.
    """
    path = Path(source)
    if not path.is_file():
        raise OpenApiParseError(f"OpenAPI spec not found: {path}")

    doc = _load_document(path)
    openapi_version = str(doc.get("openapi", ""))
    if not openapi_version.startswith("3."):
        raise OpenApiParseError(
            f"Unsupported OpenAPI version {openapi_version!r}. Only OpenAPI 3.x is supported."
        )

    info = doc.get("info", {})
    if not isinstance(info, dict):
        raise OpenApiParseError("'info' must be a mapping.")

    operations: list[OpenApiOperation] = []
    paths = doc.get("paths", {})
    if not isinstance(paths, dict):
        raise OpenApiParseError("'paths' must be a mapping.")

    for path_str, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, op in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete", "head", "options"}:
                continue
            if not isinstance(op, dict):
                continue
            operations.append(
                OpenApiOperation(
                    path=path_str,
                    method=method.lower(),
                    operation_id=_operation_id(op, method.lower(), path_str),
                    summary=_summary(op),
                    tags=_tags(op),
                )
            )

    return OpenApiSpec(
        title=str(info.get("title", "OpenAPI")),
        version=str(info.get("version", "0.0.0")),
        openapi_version=openapi_version,
        operations=tuple(operations),
    )
