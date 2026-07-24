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

# Reject specs larger than 10 MiB before reading them into memory.
_MAX_SPEC_SIZE_BYTES = 10 * 1024 * 1024


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


def _read_spec(source: Path) -> str:
    """Read the spec file, rejecting files that exceed the size limit."""
    try:
        size = source.stat().st_size
    except OSError as exc:
        raise OpenApiParseError(f"Could not inspect {source}: {exc}") from exc
    if size > _MAX_SPEC_SIZE_BYTES:
        raise OpenApiParseError(
            f"Spec too large: {source} ({size} bytes). Max allowed: {_MAX_SPEC_SIZE_BYTES}."
        )
    try:
        return source.read_text(encoding="utf-8")
    except OSError as exc:
        raise OpenApiParseError(f"Could not read {source}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise OpenApiParseError(f"Could not decode {source} as UTF-8: {exc}") from exc


def _load_document(source: Path) -> dict[str, Any]:
    text = _read_spec(source)
    suffix = source.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        try:
            import yaml  # noqa: PLC0415 - optional extra.
        except ImportError as exc:
            raise OpenApiParseError(
                "YAML support requires the 'openapi' extra. "
                "Install it with: pip install behave-gen[openapi]"
            ) from exc
        try:
            loaded = yaml.safe_load(text)
        except Exception as exc:  # noqa: BLE001 - yaml can raise many exception types.
            raise OpenApiParseError(f"Could not parse {source}: {exc}") from exc
    elif suffix == ".json":
        try:
            loaded = json.loads(text)
        except json.JSONDecodeError as exc:
            raise OpenApiParseError(f"Could not parse {source}: {exc}") from exc
    else:
        # Try JSON first, then YAML.
        try:
            loaded = json.loads(text)
        except json.JSONDecodeError as json_exc:
            try:
                import yaml  # noqa: PLC0415 - optional extra.
            except ImportError as exc:
                raise OpenApiParseError("YAML support requires the 'openapi' extra.") from exc
            try:
                loaded = yaml.safe_load(text)
            except Exception as yaml_exc:  # noqa: BLE001 - yaml can raise many exceptions.
                raise OpenApiParseError(f"Could not parse {source}: {yaml_exc}") from json_exc
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
    return f"{method}_{cleaned}" if cleaned else method


def _summary(op: dict[str, Any]) -> str:
    summary = op.get("summary")
    if isinstance(summary, str) and summary:
        return summary
    desc = op.get("description")
    if isinstance(desc, str) and desc:
        lines = desc.splitlines()
        return lines[0] if lines else ""
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
    openapi_version = doc.get("openapi")
    if not isinstance(openapi_version, str) or not openapi_version.startswith("3."):
        version_repr = repr(openapi_version) if openapi_version is not None else "<missing>"
        raise OpenApiParseError(
            f"Unsupported OpenAPI version {version_repr}. Only OpenAPI 3.x is supported."
        )

    info = doc.get("info", {})
    if not isinstance(info, dict):
        raise OpenApiParseError("'info' must be a mapping.")

    operations: list[OpenApiOperation] = []
    paths = doc.get("paths", {})
    if not isinstance(paths, dict):
        raise OpenApiParseError("'paths' must be a mapping.")

    for path_str, path_item in paths.items():
        if not isinstance(path_str, str) or not isinstance(path_item, dict):
            continue
        for method, op in path_item.items():
            if not isinstance(method, str):
                continue
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
