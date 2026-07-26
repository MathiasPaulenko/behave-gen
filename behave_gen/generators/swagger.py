"""Swagger generator for behave-gen.

Implements the :class:`Generator` protocol by converting Swagger 2.0 specs to
OpenAPI 3.x in memory and delegating to :class:`OpenApiGenerator`.
"""

from __future__ import annotations

from pathlib import Path

from behave_gen.generators.base import GenerationResult
from behave_gen.generators.openapi import OpenApiGenerator
from behave_gen.plugins.swagger import SwaggerParseError, convert_swagger_to_openapi


class SwaggerGenerator:
    """Generator for Swagger 2.0 specs."""

    def can_handle(self, source: Path, config: dict[str, object] | None = None) -> bool:  # noqa: ARG002
        """Return True if ``source`` looks like a Swagger 2.0 document."""
        if not source.is_file():
            return False
        try:
            convert_swagger_to_openapi(source)
        except SwaggerParseError:
            return False
        return True

    def generate(  # noqa: PLR0913 - matches Generator protocol
        self,
        source: Path,
        out_dir: Path,
        *,
        step_lib: str | None = None,
        tag: str | None = None,
        default_tags: tuple[str, ...] = (),
        include_paths: list[str] | None = None,
        include_methods: list[str] | None = None,
        project_name: str | None = None,
    ) -> GenerationResult:
        """Generate features and optional steps from a Swagger 2.0 spec."""
        spec = convert_swagger_to_openapi(source)
        generator = OpenApiGenerator()
        return generator._generate(  # noqa: SLF001 - delegation within the same package
            spec,
            out_dir,
            step_lib=step_lib,
            tag=tag,
            default_tags=default_tags,
            project_name=project_name,
            include_paths=include_paths,
            include_methods=include_methods,
        )
