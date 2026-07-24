"""Code generators for behave-gen.

Each generator turns an external contract (OpenAPI, Postman, Swagger, Cucumber)
into Behave ``.feature`` files and optional step definitions.
"""

from __future__ import annotations

from behave_gen.generators.base import GenerationResult, Generator

__all__ = ["GenerationResult", "Generator"]
