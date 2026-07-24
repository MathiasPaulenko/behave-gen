"""Generator protocol and shared result types.

A :class:`Generator` turns a single source file into a set of Behave artifacts
(``.feature`` files and optional step definitions). Generators are pluggable:
new sources can be added without changing the CLI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class GenerationResult:
    """Outcome of a generator run."""

    features: tuple[Path, ...] = field(default_factory=tuple)
    steps: tuple[Path, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def written_files(self) -> tuple[Path, ...]:
        """All files written by the generator."""
        return (*self.features, *self.steps)


@runtime_checkable
class Generator(Protocol):
    """Protocol implemented by all code generators."""

    def can_handle(self, source: Path, config: dict[str, Any] | None = None) -> bool:
        """Return True if this generator can process ``source``."""
        ...

    def generate(  # noqa: PLR0913 - protocol contract
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
        """Generate Behave artifacts from ``source`` into ``out_dir``."""
        ...
