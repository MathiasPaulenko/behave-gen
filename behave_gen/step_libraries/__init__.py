"""Built-in step libraries for behave-gen.

Each module here is a *template* for a real step-definition file that gets
copied into a generated project's ``features/steps/`` directory. The templates
contain concrete, runnable implementations — never empty ``pass`` skeletons
(see ``ref/adr/0001-no-empty-step-skeletons.md``).
"""

from __future__ import annotations

import string
from importlib import resources
from pathlib import Path


def http_template() -> str:
    """Return the built-in HTTP step library template source."""
    with resources.as_file(resources.files(__name__).joinpath("http_steps.py.tpl")) as p:
        return Path(p).read_text(encoding="utf-8")


def build_http_step_module(project_name: str = "generated_project") -> str:
    """Render the generic HTTP step library for the given project name."""
    raw = http_template()
    try:
        return string.Template(raw).substitute(project_name=project_name)
    except KeyError as exc:
        key = exc.args[0] if exc.args else "<unknown>"
        raise ValueError(f"Missing template variable ${key}.") from exc
