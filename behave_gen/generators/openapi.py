"""OpenAPI generator for behave-gen.

Implements the :class:`Generator` protocol for OpenAPI 3.x specs. Produces
``.feature`` files grouped by path and an optional concrete HTTP step library.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from behave_gen.generators.base import GenerationResult
from behave_gen.paths import safe_write_text
from behave_gen.plugins.openapi import build_features, build_steps, parse_openapi
from behave_gen.plugins.openapi.parser import OpenApiParseError


class OpenApiGenerator:
    """Generator for OpenAPI 3.x specs."""

    def can_handle(self, source: Path, config: dict[str, object] | None = None) -> bool:  # noqa: ARG002
        """Return True if ``source`` looks like an OpenAPI 3.x document."""
        if not source.is_file():
            return False
        try:
            spec = parse_openapi(source)
        except OpenApiParseError:
            return False
        return spec.openapi_version.startswith("3.")

    def generate(  # noqa: PLR0913 - matches Generator protocol
        self,
        source: Path,
        out_dir: Path,
        *,
        step_lib: str | None = None,
        tag: str | None = None,
        default_tags: tuple[str, ...] = (),
        include_paths: list[str] | None = None,
        include_methods: list[str] | None = None,
    ) -> GenerationResult:
        """Generate features and optional steps from an OpenAPI spec file."""
        spec = parse_openapi(source)
        return self._generate(
            spec,
            out_dir,
            step_lib=step_lib,
            tag=tag,
            default_tags=default_tags,
            project_name=out_dir.name,
            include_paths=include_paths,
            include_methods=include_methods,
        )

    def _generate(  # noqa: PLR0913
        self,
        spec: Any,
        out_dir: Path,
        *,
        step_lib: str | None = None,
        tag: str | None = None,
        default_tags: tuple[str, ...] = (),
        project_name: str = "openapi_project",
        include_paths: list[str] | None = None,
        include_methods: list[str] | None = None,
    ) -> GenerationResult:
        """Generate features and optional steps from an in-memory spec."""
        features_dir = out_dir / "features"
        steps_dir = features_dir / "steps"
        features_dir.mkdir(parents=True, exist_ok=True)

        feature_map = build_features(
            spec,
            tag=tag,
            default_tags=default_tags,
            include_paths=include_paths,
            include_methods=include_methods,
        )

        written_features: list[Path] = []
        for filename, content in feature_map.items():
            target = features_dir / f"{filename}.feature"
            safe_write_text(target, content)
            written_features.append(target)

        written_steps: list[Path] = []
        if step_lib == "http":
            steps_dir.mkdir(parents=True, exist_ok=True)
            steps_text = build_steps(spec, project_name=project_name)
            steps_file = steps_dir / "http_steps.py"
            safe_write_text(steps_file, steps_text)
            written_steps.append(steps_file)

        warnings: list[str] = []
        if not feature_map:
            warnings.append("No operations matched the given filters.")

        return GenerationResult(
            features=tuple(written_features),
            steps=tuple(written_steps),
            warnings=tuple(warnings),
        )
