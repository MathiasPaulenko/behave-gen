"""``behave-gen lint`` command implementation.

Delegates to the ``behave-lint`` CLI when the ``lint`` extra is installed.
Prints an install hint and exits gracefully when the extra is missing.
"""

from __future__ import annotations

import subprocess  # nosec B404
import sys
from pathlib import Path

from behave_gen.config import BehaveGenConfig
from behave_gen.diagnostics import check_extra
from behave_gen.paths import resolve_path, resolve_project_root
from behave_gen.project import Project, ProjectError


def run_lint(
    project_root: str | Path | None = None,
    *,
    fix: bool = False,
    paths: list[str] | None = None,
    config: BehaveGenConfig | None = None,
) -> int:
    """CLI entry point for ``behave-gen lint``.

    Args:
        project_root: Project root (defaults to cwd).
        fix: When True, pass ``--fix`` to behave-lint.
        paths: Optional explicit paths to lint; defaults to the features dir.
        config: Optional explicit behave-gen config.

    Returns:
        The behave-lint exit code, or ``0`` when the extra is missing.

    """
    root = resolve_project_root(project_root)
    try:
        project = Project.from_root(root, config=config)
    except ProjectError as exc:
        print(f"lint: {exc}", file=sys.stderr)
        return 1

    status = check_extra("lint")
    if not status.available:
        print(f"behave-lint is not installed. Install it with: {status.install_hint}")
        return 0

    if paths:
        targets: list[str] = []
        for p in paths:
            target = resolve_path(p, project.root)
            if not target.is_relative_to(project.root):
                print(
                    f"lint: Path {target} must be inside project root {project.root}",
                    file=sys.stderr,
                )
                return 1
            targets.append(str(target))
    else:
        targets = [str(project.features_dir)]

    cmd = [sys.executable, "-m", "behave_lint", "--no-color"]
    if fix:
        cmd.append("--fix")
    cmd.append("--")
    cmd.extend(targets)

    proc = subprocess.run(cmd, cwd=project.root, check=False)  # nosec B603 # noqa: S603
    return proc.returncode
