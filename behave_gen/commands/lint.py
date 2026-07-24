"""``behave-gen lint`` command implementation.

Delegates to the ``behave-lint`` CLI when the ``lint`` extra is installed.
Prints an install hint and exits gracefully when the extra is missing.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from behave_gen.diagnostics import check_extra


def run_lint(
    project_root: str | Path | None = None,
    *,
    fix: bool = False,
    paths: list[str] | None = None,
) -> int:
    """CLI entry point for ``behave-gen lint``.

    Args:
        project_root: Project root (defaults to cwd).
        fix: When True, pass ``--fix`` to behave-lint.
        paths: Optional explicit paths to lint; defaults to the features dir.

    Returns:
        The behave-lint exit code, or ``0`` when the extra is missing.
    """
    root = Path(project_root) if project_root is not None else Path.cwd()
    if not root.is_dir():
        print(f"lint: Project root not found: {root}", file=sys.stderr)
        return 1

    status = check_extra("lint")
    if not status.available:
        print(f"behave-lint is not installed. Install it with: {status.install_hint}")
        return 0

    targets = paths if paths else [str(root / "features")]
    cmd = [sys.executable, "-m", "behave_lint", "--no-color", *targets]
    if fix:
        cmd.append("--fix")

    proc = subprocess.run(cmd, cwd=root, check=False)
    return proc.returncode
