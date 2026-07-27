"""Project model for behave-gen.

A :class:`Project` describes a Behave project on disk: its root, the
``features/`` and ``features/steps/`` directories, the ``environment.py`` file,
the behave config file, and the templates directory.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from behave_gen.config import BehaveGenConfig, load_config
from behave_gen.paths import resolve_path

__all__ = ["Project", "ProjectError", "discover_project", "find_project_root"]

_PROJECT_MARKERS = ("pyproject.toml", "behave.toml")


class ProjectError(Exception):
    """Raised when a project cannot be loaded or configured."""


@dataclass(frozen=True, slots=True)
class Project:
    """Immutable description of a Behave project on disk.

    All paths are absolute and resolved.
    """

    root: Path
    features_dir: Path
    steps_dir: Path
    environment_file: Path
    config_file: Path
    templates_dir: Path
    config: BehaveGenConfig

    @classmethod
    def from_root(cls, root: str | Path, config: BehaveGenConfig | None = None) -> Project:
        """Build a :class:`Project` from an explicit root directory.

        Args:
            root: Project root directory.
            config: Optional pre-loaded config. Loaded from ``root`` if absent.

        Raises:
            ProjectError: If ``root`` is not a directory, the configuration is
                invalid, or it cannot be read.

        """
        try:
            root_path = resolve_path(root)
            if not root_path.is_dir():
                raise ProjectError(f"Project root not found: {root_path}")
            resolved_config = config if config is not None else load_config(root_path)
        except (OSError, RuntimeError, ValueError) as exc:
            raise ProjectError(str(exc)) from exc

        # Resolve config paths as absolute with .. normalization, but don't
        # follow symlinks on the final component so a symlinked environment.py
        # doesn't trigger a false "escapes project root" error.
        def _abs(path: str, base: Path) -> Path:
            p = Path(path)
            if not p.is_absolute():
                p = base / p
            # Resolve parent to normalize .. but don't follow final-component symlinks.
            return p.parent.resolve(strict=False) / p.name

        features = _abs(resolved_config.features_dir, root_path)
        steps = _abs(resolved_config.steps_dir, root_path)
        env = _abs(resolved_config.environment_file, root_path)
        templates = _abs(resolved_config.templates_dir, root_path)

        instance = cls(
            root=root_path,
            features_dir=features,
            steps_dir=steps,
            environment_file=env,
            config_file=root_path / "behave.toml",
            templates_dir=templates,
            config=resolved_config,
        )
        for attr in ("features_dir", "steps_dir", "environment_file", "templates_dir"):
            value = getattr(instance, attr)
            if not value.is_relative_to(root_path):
                raise ProjectError(f"Config path {attr}={value} escapes project root {root_path}.")
        return instance


def find_project_root(start: str | Path) -> Path:
    """Search upward from ``start`` for a project marker.

    The first directory containing ``pyproject.toml`` or ``behave.toml`` is
    returned.

    Args:
        start: Directory to start searching from.

    Returns:
        The resolved project root directory.

    Raises:
        FileNotFoundError: If no project marker is found up to the filesystem
            root.

    """
    current = resolve_path(start)
    if current.is_file():
        current = current.parent

    for candidate in (current, *current.parents):
        if any((candidate / marker).is_file() for marker in _PROJECT_MARKERS):
            return candidate

    raise FileNotFoundError(
        f"No project marker ({', '.join(_PROJECT_MARKERS)}) found "
        f"starting from {resolve_path(start)}."
    )


def discover_project(start: str | Path) -> Project:
    """Find the project root from ``start`` and build a :class:`Project`."""
    root = find_project_root(start)
    return Project.from_root(root)
