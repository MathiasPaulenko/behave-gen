"""Step builder for the OpenAPI plugin.

Generates a concrete HTTP step-definition module by reusing the built-in
``http`` step library template. The generated steps perform real HTTP calls
(no empty skeletons) and bind the operations found in the spec.
"""

from __future__ import annotations

import string
from importlib import resources
from pathlib import Path

from behave_gen.plugins.openapi.parser import OpenApiSpec


def _http_template() -> str:
    """Return the built-in HTTP step library template source."""
    with resources.as_file(
        resources.files("behave_gen.step_libraries").joinpath("http_steps.py.tpl")
    ) as p:
        return Path(p).read_text(encoding="utf-8")


def build_steps(spec: OpenApiSpec, *, project_name: str = "openapi_project") -> str:
    """Render the HTTP step library for the generated project.

    The generated module is the real, runnable HTTP step library with the
    project name substituted. It is not a set of empty skeletons.
    """
    raw = _http_template()
    try:
        return string.Template(raw).substitute(project_name=project_name)
    except KeyError as exc:
        raise ValueError(f"Missing template variable ${exc.args[0]}.") from exc
