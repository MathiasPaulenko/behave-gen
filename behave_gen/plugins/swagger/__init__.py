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


class SwaggerParseError(Exception):
    """Raised when a Swagger 2.0 document cannot be converted."""


def _load_swagger(source: Path) -> dict[str, Any]:
    text = source.read_text(encoding="utf-8")
    suffix = source.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        try:
            import yaml  # noqa: PLC0415 - optional extra.
        except ImportError as exc:
            raise SwaggerParseError("YAML support requires the 'openapi' extra.") from exc
        loaded = yaml.safe_load(text)
    else:
        try:
            loaded = json.loads(text)
        except json.JSONDecodeError:
            try:
                import yaml  # noqa: PLC0415 - optional extra.
            except ImportError as exc:
                raise SwaggerParseError("YAML support requires the 'openapi' extra.") from exc
            loaded = yaml.safe_load(text)
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
    swagger_version = str(doc.get("swagger", ""))
    if swagger_version != "2.0":
        raise SwaggerParseError(
            f"Unsupported Swagger version {swagger_version!r}. Only 2.0 is supported."
        )

    # Minimal conversion: rewrite the version key. Path items are structurally
    # compatible between Swagger 2.0 and OpenAPI 3.x for our purposes.
    converted = dict(doc)
    converted.pop("swagger", None)
    converted["openapi"] = "3.0.3"

    # Write the converted doc to a temp file and parse it.
    import tempfile  # noqa: PLC0415 - local import avoids module-level cost.

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as tmp:
        json.dump(converted, tmp)
        tmp_path = Path(tmp.name)

    try:
        return parse_openapi(tmp_path)
    except OpenApiParseError as exc:
        raise SwaggerParseError(f"Conversion failed: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)
