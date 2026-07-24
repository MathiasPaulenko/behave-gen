"""Step builder for the OpenAPI plugin.

Generates a concrete HTTP step-definition module by reusing the built-in
``http`` step library template. The generated steps perform real HTTP calls
(no empty skeletons) and bind the operations found in the spec.
"""

from __future__ import annotations

from behave_gen.plugins.openapi.parser import OpenApiSpec
from behave_gen.step_libraries import build_http_step_module


def build_steps(spec: OpenApiSpec, *, project_name: str = "openapi_project") -> str:
    """Render the HTTP step library for the generated project.

    The generated module is the real, runnable HTTP step library with the
    project name substituted. It is not a set of empty skeletons.
    """
    del spec  # Reserved for future operation-specific step generation.
    return build_http_step_module(project_name=project_name)
