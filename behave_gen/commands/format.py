"""``behave-gen format`` command implementation.

Delegates to the ``behave-format`` CLI when the ``format`` extra is installed.
Prints an install hint and exits gracefully when the extra is missing.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from behave_gen.config import BehaveGenConfig
from behave_gen.diagnostics import check_extra
from behave_gen.paths import resolve_project_root
from behave_gen.project import Project, ProjectError


def run_format(
    project_root: str | Path | None = None,
    *,
    check: bool = False,
    paths: list[str] | None = None,
    config: BehaveGenConfig | None = None,
) -> int:
    """CLI entry point for ``behave-gen format``.

    Args:
        project_root: Project root (defaults to cwd).
        check: When True, pass ``--check`` to behave-format (no writes).
        paths: Optional explicit paths to format; defaults to the features dir.

    Returns:
        The behave-format exit code, or ``0`` when the extra is missing.
    """
    root = resolve_project_root(project_root)
    try:
        project = Project.from_root(root, config=config)
    except ProjectError as exc:
        print(f"format: {exc}", file=sys.stderr)
        return 1

    status = check_extra("format")
    if not status.available:
        print(f"behave-format is not installed. Install it with: {status.install_hint}")
        return 0

    targets = paths if paths else [str(project.features_dir)]
    cmd = [sys.executable, "-m", "behave_format", *targets]
    if check:
        cmd.append("--check")

    proc = subprocess.run(cmd, cwd=project.root, check=False)
    return proc.returncode
