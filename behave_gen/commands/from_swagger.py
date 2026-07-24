"""``behave-gen from-swagger`` command implementation.

Converts a Swagger 2.0 spec to OpenAPI 3.x in memory, then reuses the OpenAPI
generator to produce features and steps.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from behave_gen.plugins.openapi import build_features, build_steps
from behave_gen.plugins.swagger import SwaggerParseError, convert_swagger_to_openapi


@dataclass(frozen=True, slots=True)
class FromSwaggerOptions:
    """Options for ``from-swagger``."""

    spec: str
    out_dir: str = "features"
    step_lib: str | None = None
    tag: str | None = None
    include_paths: tuple[str, ...] = ()
    include_methods: tuple[str, ...] = ()


def run_from_swagger(
    options: FromSwaggerOptions,
    project_root: str | Path | None = None,
) -> int:
    """CLI entry point for ``behave-gen from-swagger``."""
    root = Path(project_root) if project_root is not None else Path.cwd()
    spec_path = Path(options.spec)
    if not spec_path.is_absolute():
        spec_path = (root / spec_path).resolve()

    out_dir = Path(options.out_dir)
    if not out_dir.is_absolute():
        out_dir = (root / out_dir).resolve()

    try:
        spec = convert_swagger_to_openapi(spec_path)
    except SwaggerParseError as exc:
        print(f"from-swagger: {exc}", file=sys.stderr)
        return 1

    features_dir = out_dir / "features"
    steps_dir = features_dir / "steps"
    features_dir.mkdir(parents=True, exist_ok=True)

    feature_map = build_features(
        spec,
        tag=options.tag,
        include_paths=list(options.include_paths) or None,
        include_methods=list(options.include_methods) or None,
    )

    written_features: list[Path] = []
    for filename, content in feature_map.items():
        target = features_dir / f"{filename}.feature"
        target.write_text(content, encoding="utf-8")
        written_features.append(target)

    written_steps: list[Path] = []
    if options.step_lib == "http":
        steps_dir.mkdir(parents=True, exist_ok=True)
        steps_text = build_steps(spec, project_name=out_dir.name)
        steps_file = steps_dir / "http_steps.py"
        steps_file.write_text(steps_text, encoding="utf-8")
        written_steps.append(steps_file)

    for feature in written_features:
        print(f"Created feature {feature}")
    for steps_file in written_steps:
        print(f"Created step library {steps_file}")
    return 0
