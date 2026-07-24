"""``behave-gen migrate`` command implementation.

Migrates a Cucumber project to a Behave project layout by copying feature
files and emitting a migration report.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from behave_gen.config import BehaveGenConfig
from behave_gen.paths import resolve_project_root
from behave_gen.plugins.cucumber import migrate_cucumber
from behave_gen.plugins.cucumber.migrator import MigrationError
from behave_gen.project import Project, ProjectError


class MigrateError(Exception):
    """User-facing error raised by ``migrate``."""


@dataclass(frozen=True, slots=True)
class MigrateOptions:
    """Options for ``migrate``."""

    source: str
    out_dir: str = "migrated"


def run_migrate(
    options: MigrateOptions,
    project_root: str | Path | None = None,
    *,
    config: BehaveGenConfig | None = None,
) -> int:
    """CLI entry point for ``behave-gen migrate``."""
    root = resolve_project_root(project_root)
    try:
        project = Project.from_root(root, config=config)
    except ProjectError as exc:
        print(f"migrate: {exc}", file=sys.stderr)
        return 1

    source = Path(options.source)
    if not source.is_absolute():
        source = (project.root / source).resolve()

    out_dir = Path(options.out_dir)
    if not out_dir.is_absolute():
        out_dir = (project.root / out_dir).resolve()
    if not out_dir.is_relative_to(project.root):
        print(
            f"migrate: Output directory must be inside project root: {out_dir}",
            file=sys.stderr,
        )
        return 1

    try:
        report = migrate_cucumber(source, out_dir)
    except MigrationError as exc:
        print(f"migrate: {exc}", file=sys.stderr)
        return 1

    for feature in report.features:
        print(f"Migrated feature {feature}")
    for skipped in report.skipped:
        print(f"migrate: skipped {skipped}", file=sys.stderr)
    for warning in report.warnings:
        print(f"migrate: warning: {warning}", file=sys.stderr)
    print(f"\nMigrated {len(report.features)} feature file(s).")
    return 0
