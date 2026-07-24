"""Swagger 2.0 to OpenAPI 3.x converter.

Swagger 2.0 specs cannot be consumed directly by the OpenAPI generator. This
module performs a minimal, in-memory conversion sufficient for feature
generation: it rewrites the top-level ``swagger`` key to ``openapi`` and
adjusts path item structure where needed. It does not attempt full fidelity
conversion — only what the feature builder requires.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from behave_gen.plugins.openapi.parser import OpenApiParseError, OpenApiSpec, parse_openapi

__all__ = ["SwaggerParseError", "convert_swagger_to_openapi"]

# Reject specs larger than 10 MiB before reading them into memory.
_MAX_SPEC_SIZE_BYTES = 10 * 1024 * 1024


class SwaggerParseError(Exception):
    """Raised when a Swagger 2.0 document cannot be converted."""


def _read_swagger(source: Path) -> str:
    """Read the Swagger spec file, rejecting files that exceed the size limit."""
    try:
        size = source.stat().st_size
    except OSError as exc:
        raise SwaggerParseError(f"Could not inspect {source}: {exc}") from exc
    if size > _MAX_SPEC_SIZE_BYTES:
        raise SwaggerParseError(
            f"Spec too large: {source} ({size} bytes). Max allowed: {_MAX_SPEC_SIZE_BYTES}."
        )
    try:
        return source.read_text(encoding="utf-8")
    except OSError as exc:
        raise SwaggerParseError(f"Could not read {source}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise SwaggerParseError(f"Could not decode {source} as UTF-8: {exc}") from exc


def _load_swagger(source: Path) -> dict[str, Any]:
    text = _read_swagger(source)
    suffix = source.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        try:
            import yaml  # noqa: PLC0415 - optional extra.
        except ImportError as exc:
            raise SwaggerParseError("YAML support requires the 'openapi' extra.") from exc
        try:
            loaded = yaml.safe_load(text)
        except Exception as exc:  # noqa: BLE001 - yaml can raise many exception types.
            raise SwaggerParseError(f"Could not parse {source}: {exc}") from exc
    elif suffix == ".json":
        try:
            loaded = json.loads(text)
        except json.JSONDecodeError as exc:
            raise SwaggerParseError(f"Invalid JSON in {source}: {exc}") from exc
    else:
        try:
            loaded = json.loads(text)
        except json.JSONDecodeError:
            try:
                import yaml  # noqa: PLC0415 - optional extra.
            except ImportError as exc:
                raise SwaggerParseError("YAML support requires the 'openapi' extra.") from exc
            try:
                loaded = yaml.safe_load(text)
            except Exception as yaml_exc:  # noqa: BLE001
                raise SwaggerParseError(f"Could not parse {source}: {yaml_exc}") from yaml_exc
    if not isinstance(loaded, dict):
        raise SwaggerParseError("Expected a mapping at the top level.")
    return loaded


def convert_swagger_to_openapi(source: str | Path) -> OpenApiSpec:
    """Convert a Swagger 2.0 document to an :class:`OpenApiSpec`.

    The conversion is minimal: it rewrites ``swagger: "2.0"`` to
    ``openapi: "3.0.3"`` and parses the result with the OpenAPI parser. Path
    items are already structurally compatible for feature generation purposes.

    Raises:
        SwaggerParseError: If the document is missing or not Swagger 2.0.
    """
    path = Path(source)
    if not path.is_file():
        raise SwaggerParseError(f"Swagger spec not found: {path}")

    doc = _load_swagger(path)
    swagger_version = doc.get("swagger")
    if not isinstance(swagger_version, str) or swagger_version != "2.0":
        version_repr = repr(swagger_version) if swagger_version is not None else "<missing>"
        raise SwaggerParseError(
            f"Unsupported Swagger version {version_repr}. Only 2.0 is supported."
        )

    # Minimal conversion: rewrite the version key. Path items are structurally
    # compatible between Swagger 2.0 and OpenAPI 3.x for our purposes.
    converted = dict(doc)
    converted.pop("swagger", None)
    converted["openapi"] = "3.0.3"

    # Write the converted doc to a temp file inside a private temp directory and parse it.
    import tempfile  # noqa: PLC0415 - local import avoids module-level cost.

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / "converted.json"
        try:
            with tmp_path.open("w", encoding="utf-8") as handle:
                json.dump(converted, handle)
        except (OSError, TypeError, ValueError) as exc:
            raise SwaggerParseError(f"Failed to serialize converted spec: {exc}") from exc

        try:
            return parse_openapi(tmp_path)
        except OpenApiParseError as exc:
            raise SwaggerParseError(f"Conversion failed: {exc}") from exc
