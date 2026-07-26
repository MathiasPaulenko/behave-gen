"""Cucumber-to-Behave migrator.

Walks a Cucumber project directory, copies ``.feature`` files into a Behave
``features/`` layout, and produces a migration report. Java step definitions
are not translated; the report suggests using ``behave-gen add steps``.
"""

from __future__ import annotations

import fnmatch
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from behave_gen.paths import safe_write_text


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
        """Return the paths of feature files written during migration."""
        return self.features


# Cucumber-specific lines to strip: ``# language:`` is valid Gherkin but
# Cucumber projects often include Java-style comments we leave alone.
_CUCUMBER_LANGUAGE_RE = re.compile(r"^#\s*language:\s*\S+\s*$", re.MULTILINE)


def _clean_feature_text(text: str) -> str:
    """Remove Cucumber-specific directives that Behave does not understand."""
    # Strip ``# language: xx`` lines (Behave uses behave.toml or ``--lang``).
    cleaned = _CUCUMBER_LANGUAGE_RE.sub("", text)
    return cleaned


def _within_source(path: Path, source: Path) -> bool:
    """Return True if ``path`` resolves to a location inside ``source``."""
    try:
        resolved = path.resolve()
    except (OSError, RuntimeError):
        return False
    try:
        resolved.relative_to(source.resolve())
    except ValueError:
        return False
    return True


def _find_feature_files(source: Path) -> list[Path]:
    """Find all ``.feature`` files under ``source`` without following symlinks."""
    try:
        source_is_file = source.is_file()
        source_is_dir = source.is_dir()
    except OSError:
        return []
    if source_is_file and source.suffix == ".feature":
        return [source]
    if not source_is_dir:
        return []
    files: list[Path] = []
    try:
        for root, _dirs, filenames in os.walk(source, followlinks=False):
            for filename in filenames:
                if filename.endswith(".feature"):
                    p = Path(root) / filename
                    if _within_source(p, source):
                        files.append(p.resolve())
    except OSError:
        return []
    return sorted(files)


def _find_step_definitions(source: Path) -> list[Path]:
    """Find Java step definition files (best-effort heuristic)."""
    try:
        source_is_dir = source.is_dir()
    except OSError:
        return []
    if not source_is_dir:
        return []
    patterns = ("*Steps*.java", "*StepDefs*.java", "*StepDefinitions*.java")
    candidates: list[Path] = []
    try:
        for root, _dirs, filenames in os.walk(source, followlinks=False):
            for filename in filenames:
                if any(fnmatch.fnmatch(filename, pat) for pat in patterns):
                    p = Path(root) / filename
                    if _within_source(p, source) and not p.is_symlink() and p.is_file():
                        candidates.append(p.resolve())
    except OSError:
        return []
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
    try:
        features_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise MigrationError(
            f"Could not create destination directory {features_dir}: {exc}"
        ) from exc

    written: list[Path] = []
    skipped: list[str] = []
    warnings: list[str] = []

    for feature_file in feature_files:
        # Single file source: use just the filename; otherwise preserve layout.
        rel = Path(feature_file.name) if src.is_file() else feature_file.relative_to(src)
        target = features_dir / rel
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            skipped.append(str(rel))
            warnings.append(f"Could not create parent directory for {rel}: {exc}")
            continue
        try:
            text = feature_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            skipped.append(str(rel))
            warnings.append(f"Could not read {rel}: {exc}")
            continue
        cleaned = _clean_feature_text(text)
        try:
            safe_write_text(target, cleaned)
        except OSError as exc:
            skipped.append(str(rel))
            warnings.append(f"Could not write {rel}: {exc}")
            continue
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
