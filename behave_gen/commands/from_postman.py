"""``behave-gen from-postman`` command implementation."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from behave_gen.generators.postman import PostmanGenerator
from behave_gen.plugins.postman.parser import PostmanParseError


@dataclass(frozen=True, slots=True)
class FromPostmanOptions:
    """Options for ``from-postman``."""

    collection: str
    out_dir: str = "features"
    step_lib: str | None = None
    tag: str | None = None


def run_from_postman(
    options: FromPostmanOptions,
    project_root: str | Path | None = None,
) -> int:
    """CLI entry point for ``behave-gen from-postman``."""
    root = Path(project_root) if project_root is not None else Path.cwd()
    collection_path = Path(options.collection)
    if not collection_path.is_absolute():
        collection_path = (root / collection_path).resolve()

    out_dir = Path(options.out_dir)
    if not out_dir.is_absolute():
        out_dir = (root / out_dir).resolve()

    generator = PostmanGenerator()
    try:
        result = generator.generate(
            collection_path,
            out_dir,
            step_lib=options.step_lib,
            tag=options.tag,
        )
    except PostmanParseError as exc:
        print(f"from-postman: {exc}", file=sys.stderr)
        return 1

    for feature in result.features:
        print(f"Created feature {feature}")
    for steps_file in result.steps:
        print(f"Created step library {steps_file}")
    for warning in result.warnings:
        print(f"from-postman: warning: {warning}", file=sys.stderr)
    return 0
