"""Path resolution helpers for behave-gen.

All helpers return absolute :class:`pathlib.Path` objects so that downstream
code never has to reason about relative vs. absolute paths.
"""

from __future__ import annotations

from pathlib import Path


def resolve_path(path: str | Path, base: str | Path | None = None) -> Path:
    """Resolve ``path`` relative to ``base`` and return an absolute path.

    Args:
        path: A path that may be relative or absolute.
        base: Base directory used to resolve relative paths. Defaults to the
            current working directory.

    Returns:
        An absolute, normalized :class:`pathlib.Path`.
    """
    candidate = Path(path)
    if not candidate.is_absolute():
        base_dir = Path(base) if base is not None else Path.cwd()
        candidate = base_dir / candidate
    return candidate.resolve()


def join(*parts: str | Path) -> Path:
    """Join path parts and return an absolute, normalized path."""
    return Path(*parts).resolve() if Path(*parts).is_absolute() else resolve_path(Path(*parts))


def ensure_directory(path: str | Path) -> Path:
    """Ensure ``path`` exists as a directory, creating it if necessary.

    Returns the resolved directory path.
    """
    resolved = resolve_path(path)
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def relative_to(path: str | Path, base: str | Path) -> Path:
    """Return ``path`` expressed relative to ``base``.

    Raises ValueError if ``path`` is not inside ``base``.
    """
    resolved_path = resolve_path(path)
    resolved_base = resolve_path(base)
    return resolved_path.relative_to(resolved_base)
