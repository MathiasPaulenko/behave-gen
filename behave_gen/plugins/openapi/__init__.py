"""OpenAPI plugin: parser, feature builder, and step builder.

The plugin is intentionally dependency-light: it parses OpenAPI 3.x documents
(YAML or JSON) using ``pyyaml`` (optional ``openapi`` extra) or the standard
``json`` module, then emits Gherkin features and reuses the built-in HTTP step
library for concrete step definitions.
"""

from __future__ import annotations

from behave_gen.plugins.openapi.feature_builder import build_features
from behave_gen.plugins.openapi.parser import (
    OpenApiOperation,
    OpenApiSpec,
    parse_openapi,
)
from behave_gen.plugins.openapi.step_builder import build_steps

__all__ = [
    "OpenApiOperation",
    "OpenApiSpec",
    "build_features",
    "build_steps",
    "parse_openapi",
]
