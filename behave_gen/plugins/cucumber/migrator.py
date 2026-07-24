"""Cucumber-to-Behave migrator.

Walks a Cucumber project directory, copies ``.feature`` files into a Behave
``features/`` layout, and produces a migration report. Java step definitions
are not translated; the report suggests using ``behave-gen add steps``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


class MigrationError(Exception):
    """User-facing error raised by the Cucumber migrator."""


@dataclass(frozen=True, slots=True)
class MigrationReport:
    """Outcome of a Cucumber-to-Behave migration."""

    features: tuple[Path, ...] = field(default_factory=tuple)
    skipped: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def written_files(self) -> tuple[Path, ...]:
        return self.features


# Cucumber-specific lines to strip: ``# language:`` is valid Gherkin but
# Cucumber projects often include Java-style comments we leave alone.
_CUCUMBER_LANGUAGE_RE = re.compile(r"^#\s*language:\s*\S+\s*$", re.MULTILINE)


def _clean_feature_text(text: str) -> str:
    """Remove Cucumber-specific directives that Behave does not understand."""
    # Strip ``# language: xx`` lines (Behave uses behave.toml or ``--lang``).
    cleaned = _CUCUMBER_LANGUAGE_RE.sub("", text)
    return cleaned


def _find_feature_files(source: Path) -> list[Path]:
    """Find all ``.feature`` files under ``source``."""
    if source.is_file() and source.suffix == ".feature":
        return [source]
    if source.is_dir():
        return sorted(source.rglob("*.feature"))
    return []


def _find_step_definitions(source: Path) -> list[Path]:
    """Find Java step definition files (best-effort heuristic)."""
    if not source.is_dir():
        return []
    candidates: list[Path] = []
    for pattern in ("**/*Steps*.java", "**/*StepDefs*.java", "**/*StepDefinitions*.java"):
        candidates.extend(source.rglob(pattern))
    return sorted(set(candidates))


def migrate_cucumber(source: str | Path, out_dir: str | Path) -> MigrationReport:
    """Migrate a Cucumber project at ``source`` into ``out_dir``.

    Args:
        source: Cucumber project root or a directory containing ``.feature``
            files.
        out_dir: Destination directory; features are written to
            ``out_dir/features/``.

    Returns:
        A :class:`MigrationReport` with the list of written feature files and
        any warnings (e.g. Java step definitions found but not translated).

    Raises:
        MigrationError: If ``source`` does not exist or contains no features.
    """
    src = Path(source).resolve()
    if not src.exists():
        raise MigrationError(f"Source not found: {src}")

    feature_files = _find_feature_files(src)
    if not feature_files:
        raise MigrationError(f"No .feature files found under {src}.")

    dest = Path(out_dir).resolve()
    features_dir = dest / "features"
    features_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    skipped: list[str] = []
    warnings: list[str] = []

    for feature_file in feature_files:
        # Single file source: use just the filename; otherwise preserve layout.
        rel = Path(feature_file.name) if src.is_file() else feature_file.relative_to(src)
        target = features_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            text = feature_file.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            skipped.append(str(rel))
            warnings.append(f"Could not read {rel}: {exc}")
            continue
        cleaned = _clean_feature_text(text)
        target.write_text(cleaned, encoding="utf-8")
        written.append(target)

    java_steps = _find_step_definitions(src)
    if java_steps:
        warnings.append(
            f"Found {len(java_steps)} Java step definition file(s). "
            "Use 'behave-gen add steps --lib <http|auth>' to generate "
            "Python step definitions."
        )

    return MigrationReport(
        features=tuple(written),
        skipped=tuple(skipped),
        warnings=tuple(warnings),
    )
