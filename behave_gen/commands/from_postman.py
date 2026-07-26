"""``behave-gen from-postman`` command implementation."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from behave_gen.config import BehaveGenConfig
from behave_gen.generators.postman import PostmanGenerator
from behave_gen.paths import resolve_project_root
from behave_gen.plugins.postman.parser import PostmanParseError
from behave_gen.project import Project, ProjectError


@dataclass(frozen=True, slots=True)
class FromPostmanOptions:
    """Options for ``from-postman``."""

    collection: str
    out_dir: str = "gen"
    step_lib: str | None = None
    tag: str | None = None


def run_from_postman(
    options: FromPostmanOptions,
    project_root: str | Path | None = None,
    *,
    config: BehaveGenConfig | None = None,
) -> int:
    """CLI entry point for ``behave-gen from-postman``."""
    root = resolve_project_root(project_root)
    try:
        project = Project.from_root(root, config=config)
    except ProjectError as exc:
        print(f"from-postman: {exc}", file=sys.stderr)
        return 1

    collection_path = Path(options.collection)
    if not collection_path.is_absolute():
        collection_path = (project.root / collection_path).resolve()
        if not collection_path.is_relative_to(project.root):
            print(
                f"from-postman: Collection path must be inside project root: {collection_path}",
                file=sys.stderr,
            )
            return 1

    out_dir = Path(options.out_dir)
    if not out_dir.is_absolute():
        out_dir = project.root / out_dir
    out_dir = out_dir.resolve()
    if not out_dir.is_relative_to(project.root):
        print(
            f"from-postman: Output directory must be inside project root: {out_dir}",
            file=sys.stderr,
        )
        return 1

    if options.step_lib is not None and options.step_lib != "http":
        print(
            "from-postman: Only the 'http' step library is supported for generated specs.",
            file=sys.stderr,
        )
        return 1

    generator = PostmanGenerator()
    try:
        result = generator.generate(
            collection_path,
            out_dir,
            step_lib=options.step_lib,
            tag=options.tag,
            default_tags=project.config.default_tags,
            project_name=project.root.name,
        )
    except (PostmanParseError, OSError) as exc:
        print(f"from-postman: {exc}", file=sys.stderr)
        return 1

    for feature in result.features:
        print(f"Created feature {feature}")
    for steps_file in result.steps:
        print(f"Created step library {steps_file}")
    for warning in result.warnings:
        print(f"from-postman: warning: {warning}", file=sys.stderr)
    return 0
