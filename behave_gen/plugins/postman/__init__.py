"""Postman plugin: parser and feature builder.

Parses a Postman Collection (v2.1) JSON file and emits Gherkin features grouped
by Postman folder. Each request becomes one scenario using the HTTP step
library syntax.
"""

from __future__ import annotations

from behave_gen.plugins.postman.feature_builder import build_features
from behave_gen.plugins.postman.parser import (
    PostmanCollection,
    PostmanRequest,
    parse_postman,
)

__all__ = [
    "PostmanCollection",
    "PostmanRequest",
    "build_features",
    "parse_postman",
]
