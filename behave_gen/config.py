"""Configuration model for behave-gen.

Reads the ``[tool.behave-gen]`` table from ``pyproject.toml`` and exposes a
frozen, validated :class:`BehaveGenConfig` dataclass.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

CONFIG_TABLE = "behave-gen"
"""TOML table name under ``[tool.*]`` where behave-gen config lives."""

_VALID_TEMPLATE_ENGINES = frozenset({"string", "jinja2"})
_VALID_KEYS = frozenset(
    {
        "features_dir",
        "steps_dir",
        "environment_file",
        "templates_dir",
        "template_engine",
        "default_tags",
    }
)


@dataclass(frozen=True, slots=True)
class BehaveGenConfig:
    """Immutable behave-gen configuration.

    Defaults are deterministic and independent of the host environment so that
    identical inputs always produce identical projects.
    """

    features_dir: str = "features"
    steps_dir: str = "features/steps"
    environment_file: str = "environment.py"
    templates_dir: str = "templates"
    template_engine: str = "string"
    default_tags: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.template_engine not in _VALID_TEMPLATE_ENGINES:
            valid = ", ".join(sorted(_VALID_TEMPLATE_ENGINES))
            raise ValueError(
                f"Invalid template_engine {self.template_engine!r}. Valid values: {valid}."
            )

    @classmethod
    def default(cls) -> BehaveGenConfig:
        """Return the default configuration."""
        return cls()

    def with_overrides(self, **overrides: Any) -> BehaveGenConfig:  # noqa: ANN401
        """Return a new config with the given overrides applied."""
        known = {f.name for f in fields(self)}
        unknown = set(overrides) - known
        if unknown:
            raise ValueError(f"Unknown config keys: {sorted(unknown)}")
        return type(self)(**{**self.as_dict(), **overrides})

    def as_dict(self) -> dict[str, Any]:
        """Return the config as a plain dictionary."""
        return {f.name: getattr(self, f.name) for f in fields(self)}


def load_config_at(path: str | Path) -> BehaveGenConfig:
    """Load behave-gen configuration from an explicit ``pyproject.toml`` path.

    Falls back to :meth:`BehaveGenConfig.default` when the file or the
    ``[tool.behave-gen]`` table is missing.

    Args:
        path: Path to ``pyproject.toml``.

    Returns:
        A frozen :class:`BehaveGenConfig`.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        ValueError: If the file cannot be decoded as TOML or contains invalid
            configuration values.
    """
    pyproject = Path(path)
    if not pyproject.is_file():
        raise FileNotFoundError(f"Config file not found: {pyproject}")

    try:
        with pyproject.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"Could not parse {pyproject}: {exc}") from exc

    return _build_config(data)


def load_config(root: str | Path) -> BehaveGenConfig:
    """Load behave-gen configuration from ``root/pyproject.toml``.

    Falls back to :meth:`BehaveGenConfig.default` when the file or the
    ``[tool.behave-gen]`` table is missing.

    Args:
        root: Project root containing ``pyproject.toml``.

    Returns:
        A frozen :class:`BehaveGenConfig`.

    Raises:
        FileNotFoundError: If ``root`` is not a directory.
        ValueError: If the config contains unknown keys or invalid values.
    """
    root_path = Path(root)
    if not root_path.is_dir():
        raise FileNotFoundError(f"Project root not found: {root_path}")

    pyproject = root_path / "pyproject.toml"
    if not pyproject.is_file():
        return BehaveGenConfig.default()

    return load_config_at(pyproject)


def _build_config(data: dict[str, Any]) -> BehaveGenConfig:
    """Build a :class:`BehaveGenConfig` from parsed ``pyproject.toml`` data."""
    tool_section = data.get("tool", {})
    raw = tool_section.get(CONFIG_TABLE, {})
    if not raw:
        return BehaveGenConfig.default()

    if not isinstance(raw, dict):
        raise ValueError(f"[tool.{CONFIG_TABLE}] must be a table, got {type(raw).__name__}.")

    unknown = set(raw) - _VALID_KEYS
    if unknown:
        valid = ", ".join(sorted(_VALID_KEYS))
        raise ValueError(
            f"Unknown [tool.{CONFIG_TABLE}] keys: {sorted(unknown)}. Valid keys: {valid}."
        )

    overrides: dict[str, Any] = {}
    for key in _VALID_KEYS:
        if key not in raw:
            continue
        value = raw[key]
        if key == "default_tags":
            overrides[key] = _coerce_tags(value, key)
        else:
            overrides[key] = _coerce_str(value, key)

    return BehaveGenConfig.default().with_overrides(**overrides)


def _coerce_str(value: Any, key: str) -> str:  # noqa: ANN401
    if not isinstance(value, str):
        raise ValueError(
            f"[tool.{CONFIG_TABLE}] {key} must be a string, got {type(value).__name__}."
        )
    return value


def _coerce_tags(value: Any, key: str) -> tuple[str, ...]:  # noqa: ANN401
    if isinstance(value, str):
        return tuple(value.split())
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return tuple(value)
    raise ValueError(f"[tool.{CONFIG_TABLE}] {key} must be a string or list of strings.")
