"""Path resolution helpers for behave-gen.

All helpers return absolute :class:`pathlib.Path` objects so that downstream
code never has to reason about relative vs. absolute paths.
"""

from __future__ import annotations

import contextlib
import os
import sys
import uuid
from pathlib import Path

# ASCII control characters are all code points below the space character.
_CONTROL_CHAR_THRESHOLD = 32

# Windows reserved device names; even names like ``CON.txt`` are reserved.
_WIN_RESERVED_NAMES = frozenset(
    ["CON", "PRN", "AUX", "NUL"]
    + [f"COM{i}" for i in range(1, 10)]
    + [f"LPT{i}" for i in range(1, 10)]
)

__all__ = [
    "ensure_directory",
    "is_windows_reserved_name",
    "relative_to",
    "resolve_path",
    "resolve_project_root",
    "safe_write_text",
    "validate_name",
]


def is_windows_reserved_name(name: str) -> bool:
    """Return True when ``name`` (or its base before the first dot) is reserved on Windows."""
    if sys.platform != "win32":
        return False
    base = name.split(".", 1)[0].upper()
    return base in _WIN_RESERVED_NAMES


def validate_name(name: str) -> str:
    """Validate a user-supplied file or directory ``name``.

    Strips surrounding whitespace, rejects empty strings, exact ``.``/``..``,
    absolute paths, and path separator or reserved characters. Returns the
    cleaned name.

    Raises:
        ValueError: If the name is empty or would be unsafe as a path component.

    """
    cleaned = name.strip()
    if not cleaned:
        raise ValueError("Name cannot be empty or whitespace only.")
    if cleaned in {".", ".."} or all(ch == "." for ch in cleaned):
        raise ValueError("Name cannot be '.' or '..' or consist only of dots.")
    if os.path.isabs(cleaned):
        raise ValueError("Name cannot be an absolute path.")

    forbidden = {"\\", "/", ":", "*", "?", '"', "<", ">", "|", "$", "\x00"}

    if os.sep and os.sep not in forbidden:
        forbidden.add(os.sep)
    if os.altsep and os.altsep not in forbidden:
        forbidden.add(os.altsep)
    if any(ch in forbidden for ch in cleaned):
        raise ValueError(f"Name contains forbidden characters: {cleaned!r}.")
    if any(ord(ch) < _CONTROL_CHAR_THRESHOLD for ch in cleaned):
        raise ValueError("Name cannot contain control characters.")
    if cleaned.endswith("."):
        raise ValueError("Name cannot end with a period.")
    if is_windows_reserved_name(cleaned):
        raise ValueError(f"Name is reserved on Windows: {cleaned!r}.")

    return cleaned


def resolve_project_root(project_root: str | Path | None) -> Path:
    """Return ``project_root`` as an absolute :class:`Path`, defaulting to cwd."""
    if project_root is None:
        return Path.cwd()
    return Path(project_root).resolve()


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


def safe_write_text(path: str | Path, content: str) -> None:
    """Write ``content`` to ``path`` using a temporary file and atomic replace.

    The parent directory must already exist. If a symlink exists at ``path``,
    it is replaced rather than followed, preventing symlink-target overwrites.
    Output always uses LF line endings regardless of platform.
    """
    dst = Path(path)
    tmp = dst.parent / f".write-{uuid.uuid4().hex}.tmp"
    try:
        tmp.write_text(content, encoding="utf-8", newline="\n")
        tmp.replace(dst)
    finally:
        with contextlib.suppress(OSError):
            tmp.unlink(missing_ok=True)
