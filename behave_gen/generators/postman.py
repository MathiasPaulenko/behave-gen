"""Postman generator for behave-gen.

Implements the :class:`Generator` protocol for Postman Collection v2.1 files.
Produces ``.feature`` files grouped by folder and an optional concrete HTTP
step library.
"""

from __future__ import annotations

from pathlib import Path

from behave_gen.generators.base import GenerationResult
from behave_gen.paths import safe_write_text
from behave_gen.plugins.postman import build_features, parse_postman
from behave_gen.plugins.postman.parser import PostmanParseError
from behave_gen.step_libraries import build_http_step_module


class PostmanGenerator:
    """Generator for Postman Collection v2.1 files."""

    def can_handle(self, source: Path, config: dict[str, object] | None = None) -> bool:  # noqa: ARG002
        """Return True if ``source`` looks like a Postman v2.x collection."""
        if not source.is_file():
            return False
        try:
            collection = parse_postman(source)
        except PostmanParseError:
            return False
        return "v2." in collection.schema

    def generate(  # noqa: PLR0913 - matches Generator protocol
        self,
        source: Path,
        out_dir: Path,
        *,
        step_lib: str | None = None,
        tag: str | None = None,
        default_tags: tuple[str, ...] = (),
        include_paths: list[str] | None = None,  # noqa: ARG002 - not used
        include_methods: list[str] | None = None,  # noqa: ARG002 - not used
    ) -> GenerationResult:
        """Generate features and optional steps from a Postman collection."""
        collection = parse_postman(source)
        features_dir = out_dir / "features"
        steps_dir = features_dir / "steps"
        features_dir.mkdir(parents=True, exist_ok=True)

        feature_map = build_features(collection, tag=tag, default_tags=default_tags)

        written_features: list[Path] = []
        for filename, content in feature_map.items():
            target = features_dir / f"{filename}.feature"
            safe_write_text(target, content)
            written_features.append(target)

        written_steps: list[Path] = []
        if step_lib == "http":
            steps_dir.mkdir(parents=True, exist_ok=True)
            steps_text = build_http_step_module(project_name=out_dir.name)
            steps_file = steps_dir / "http_steps.py"
            safe_write_text(steps_file, steps_text)
            written_steps.append(steps_file)

        warnings: list[str] = []
        if not feature_map:
            warnings.append("No requests found in the collection.")

        return GenerationResult(
            features=tuple(written_features),
            steps=tuple(written_steps),
            warnings=tuple(warnings),
        )
