"""``behave-gen from-swagger`` command implementation.

Converts a Swagger 2.0 spec to OpenAPI 3.x in memory, then reuses the OpenAPI
generator to produce features and steps.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from behave_gen.config import BehaveGenConfig
from behave_gen.generators.swagger import SwaggerGenerator
from behave_gen.paths import resolve_project_root
from behave_gen.plugins.swagger import SwaggerParseError
from behave_gen.project import Project, ProjectError


@dataclass(frozen=True, slots=True)
class FromSwaggerOptions:
    """Options for ``from-swagger``."""

    spec: str
    out_dir: str = "gen"
    step_lib: str | None = None
    tag: str | None = None
    include_paths: tuple[str, ...] = ()
    include_methods: tuple[str, ...] = ()


def run_from_swagger(
    options: FromSwaggerOptions,
    project_root: str | Path | None = None,
    *,
    config: BehaveGenConfig | None = None,
) -> int:
    """CLI entry point for ``behave-gen from-swagger``."""
    root = resolve_project_root(project_root)
    try:
        project = Project.from_root(root, config=config)
    except ProjectError as exc:
        print(f"from-swagger: {exc}", file=sys.stderr)
        return 1

    spec_path = Path(options.spec)
    if not spec_path.is_absolute():
        spec_path = (project.root / spec_path).resolve()

    out_dir = Path(options.out_dir)
    if not out_dir.is_absolute():
        out_dir = (project.root / out_dir).resolve()
    if not out_dir.is_relative_to(project.root):
        print(
            f"from-swagger: Output directory must be inside project root: {out_dir}",
            file=sys.stderr,
        )
        return 1

    if options.step_lib is not None and options.step_lib != "http":
        print(
            "from-swagger: Only the 'http' step library is supported for generated specs.",
            file=sys.stderr,
        )
        return 1

    generator = SwaggerGenerator()
    try:
        result = generator.generate(
            spec_path,
            out_dir,
            step_lib=options.step_lib,
            tag=options.tag,
            default_tags=project.config.default_tags,
            include_paths=list(options.include_paths) or None,
            include_methods=list(options.include_methods) or None,
        )
    except (SwaggerParseError, OSError) as exc:
        print(f"from-swagger: {exc}", file=sys.stderr)
        return 1

    for feature in result.features:
        print(f"Created feature {feature}")
    for steps_file in result.steps:
        print(f"Created step library {steps_file}")
    for warning in result.warnings:
        print(f"from-swagger: warning: {warning}", file=sys.stderr)
    return 0
