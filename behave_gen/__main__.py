"""Entry point for ``python -m behave_gen``.

Delegates to the Typer CLI defined in :mod:`behave_gen.cli.app`.
"""

from __future__ import annotations

import sys

from behave_gen.cli.app import run

if __name__ == "__main__":  # pragma: no cover - entry point exercised via subprocess.
    sys.exit(run(sys.argv[1:]))
