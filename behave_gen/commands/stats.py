"""``behave-gen stats`` command implementation.

Reports counts of features, scenarios, and steps in a project using
``behave-model``.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from behave_model import ParseError, parse_feature

from behave_gen.config import BehaveGenConfig
from behave_gen.paths import resolve_project_root
from behave_gen.project import Project, ProjectError


class StatsError(Exception):
    """User-facing error raised by ``stats``."""


@dataclass(frozen=True, slots=True)
class StatsReport:
    """Aggregate statistics for a Behave project."""

    project: str
    features: int = 0
    scenarios: int = 0
    scenarios_outline: int = 0
    steps: int = 0
    tags: int = 0
    files: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dictionary representation."""
        return asdict(self)


def _feature_files(directory: Path) -> list[Path]:
    """List ``.feature`` files under ``directory`` without following symlinks."""
    files: list[Path] = []
    for root, _dirs, filenames in os.walk(directory, followlinks=False):
        for filename in filenames:
            if filename.endswith(".feature"):
                path = Path(root) / filename
                if not path.is_symlink():
                    files.append(path)
    return files


def _collect_stats(project: Project) -> StatsReport:  # noqa: PLR0912 - stats aggregation has many defensive checks.
    """Walk the project's features directory and aggregate statistics."""
    features_dir = project.features_dir
    if not features_dir.is_dir():
        return StatsReport(project=str(project.root), warnings=("No features directory found.",))

    try:
        feature_files = _feature_files(features_dir)
    except OSError as exc:
        return StatsReport(
            project=str(project.root),
            warnings=(f"Could not read features directory: {exc}",),
        )

    if not feature_files:
        return StatsReport(project=str(project.root), warnings=("No .feature files found.",))

    total_features = 0
    total_scenarios = 0
    total_outlines = 0
    total_steps = 0
    all_tags: set[str] = set()
    files: list[str] = []
    warnings: list[str] = []

    for feature_file in feature_files:
        try:
            resolved = feature_file.resolve()
        except (OSError, RuntimeError):
            continue
        if not resolved.is_file():
            continue
        if not resolved.is_relative_to(project.root):
            warnings.append(f"Skipped file outside project root: {feature_file.name}")
            continue
        try:
            text = resolved.read_text(encoding="utf-8")
            feature = parse_feature(text, filename=str(resolved))
        except ParseError as exc:
            warnings.append(f"Parse error in {feature_file.name}: {exc}")
            continue
        except UnicodeDecodeError as exc:
            warnings.append(f"Encoding error in {feature_file.name}: {exc}")
            continue
        except OSError as exc:
            warnings.append(f"Could not read {feature_file.name}: {exc}")
            continue

        total_features += 1
        files.append(str(resolved.relative_to(project.root)))
        all_tags.update(str(t) for t in getattr(feature, "tags", []) or [])
        background = getattr(feature, "background", None)
        if background:
            total_steps += len(getattr(background, "steps", []) or [])
        for scenario in getattr(feature, "scenarios", []) or []:
            total_scenarios += 1
            cls_name = type(scenario).__name__
            if cls_name == "ScenarioOutline":
                total_outlines += 1
            total_steps += len(getattr(scenario, "steps", []) or [])
            all_tags.update(str(t) for t in getattr(scenario, "tags", []) or [])

    return StatsReport(
        project=str(project.root),
        features=total_features,
        scenarios=total_scenarios,
        scenarios_outline=total_outlines,
        steps=total_steps,
        tags=len(all_tags),
        files=tuple(files),
        warnings=tuple(warnings),
    )


def run_stats(
    project_root: str | Path | None = None,
    *,
    fmt: str = "text",
    config: BehaveGenConfig | None = None,
) -> int:
    """CLI entry point for ``behave-gen stats``."""
    root = resolve_project_root(project_root)
    try:
        project = Project.from_root(root, config=config)
    except ProjectError as exc:
        print(f"stats: {exc}", file=sys.stderr)
        return 1

    fmt_normalized = fmt.lower()
    if fmt_normalized not in {"text", "json"}:
        print(f"stats: Invalid format {fmt!r}. Use 'text' or 'json'.", file=sys.stderr)
        return 1

    report = _collect_stats(project)

    if fmt_normalized == "json":
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return 0

    print(f"Project: {report.project}")
    print(f"  Features:         {report.features}")
    print(f"  Scenarios:        {report.scenarios}")
    print(f"  Scenario outlines: {report.scenarios_outline}")
    print(f"  Steps:            {report.steps}")
    print(f"  Tags:             {report.tags}")
    print(f"  Files:            {len(report.files)}")
    for warning in report.warnings:
        print(f"  warning: {warning}", file=sys.stderr)
    return 0
