"""``behave-gen from-openapi`` command implementation.

Wraps the :class:`OpenApiGenerator` and exposes it through the CLI.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from behave_gen.generators.openapi import OpenApiGenerator
from behave_gen.paths import resolve_project_root
from behave_gen.plugins.openapi.parser import OpenApiParseError


@dataclass(frozen=True, slots=True)
class FromOpenApiOptions:
    """Options for ``from-openapi``."""

    spec: str
    out_dir: str = "gen"
    step_lib: str | None = None
    tag: str | None = None
    include_paths: tuple[str, ...] = ()
    include_methods: tuple[str, ...] = ()


def run_from_openapi(
    options: FromOpenApiOptions,
    project_root: str | Path | None = None,
) -> int:
    """CLI entry point for ``behave-gen from-openapi``."""
    root = resolve_project_root(project_root)
    spec_path = Path(options.spec)
    if not spec_path.is_absolute():
        spec_path = (root / spec_path).resolve()

    out_dir = Path(options.out_dir)
    if not out_dir.is_absolute():
        out_dir = (root / out_dir).resolve()

    if options.step_lib is not None and options.step_lib != "http":
        print(
            "from-openapi: Only the 'http' step library is supported for generated specs.",
            file=sys.stderr,
        )
        return 1

    generator = OpenApiGenerator()
    try:
        result = generator.generate(
            spec_path,
            out_dir,
            step_lib=options.step_lib,
            tag=options.tag,
            include_paths=list(options.include_paths) or None,
            include_methods=list(options.include_methods) or None,
        )
    except OpenApiParseError as exc:
        print(f"from-openapi: {exc}", file=sys.stderr)
        return 1

    for feature in result.features:
        print(f"Created feature {feature}")
    for steps_file in result.steps:
        print(f"Created step library {steps_file}")
    for warning in result.warnings:
        print(f"from-openapi: warning: {warning}", file=sys.stderr)
    return 0
