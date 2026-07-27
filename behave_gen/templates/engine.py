"""Template engine abstraction for behave-gen.

Provides a :class:`TemplateEngine` protocol with two implementations:

- :class:`StringTemplateEngine`: default, uses :class:`string.Template` and
  ``$name`` placeholders. Zero extra dependencies.
- :class:`Jinja2Engine`: optional, used only when the ``jinja2`` extra is
  installed.

Missing placeholders raise :class:`TemplateRenderError` with the offending
filename so users can locate the problem quickly.
"""

from __future__ import annotations

import string
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from behave_gen.paths import safe_write_text

if TYPE_CHECKING:
    import jinja2


class TemplateRenderError(Exception):
    """Raised when a template cannot be rendered."""


class TemplateEngine(Protocol):
    """Protocol implemented by all template engines."""

    def render(self, source: str, context: dict[str, Any], *, filename: str | None = None) -> str:
        """Render ``source`` with ``context`` and return the result."""
        ...

    def render_file(self, src: Path, dst: Path, context: dict[str, Any]) -> None:
        """Render the file at ``src`` into ``dst`` preserving nothing but content."""
        ...


@dataclass(frozen=True, slots=True)
class StringTemplateEngine:
    """Render templates using :class:`string.Template` (``$name`` placeholders)."""

    def render(self, source: str, context: dict[str, Any], *, filename: str | None = None) -> str:
        """Render ``source`` using :class:`string.Template` with ``context``."""
        template = string.Template(source)
        try:
            return template.substitute(context)
        except KeyError as exc:
            key = exc.args[0]
            raise TemplateRenderError(
                f"Missing template variable ${key}" + (f" in {filename}" if filename else "")
            ) from exc
        except ValueError as exc:
            raise TemplateRenderError(
                f"Invalid template placeholder: {exc}" + (f" in {filename}" if filename else "")
            ) from exc

    def render_file(self, src: Path, dst: Path, context: dict[str, Any]) -> None:
        """Read ``src``, render it, and write the result to ``dst``."""
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            try:
                text = src.read_text(encoding="utf-8")
            except UnicodeDecodeError as exc:
                raise TemplateRenderError(f"Could not decode {src} as UTF-8: {exc}") from exc
            safe_write_text(dst, self.render(text, context, filename=str(src)))
        except OSError as exc:
            raise TemplateRenderError(f"Could not render {src} to {dst}: {exc}") from exc


@dataclass(frozen=True, slots=True)
class Jinja2Engine:
    """Render templates using jinja2 (``{{ name }}`` placeholders)."""

    environment: jinja2.Environment

    def render(self, source: str, context: dict[str, Any], *, filename: str | None = None) -> str:
        """Render ``source`` using the jinja2 environment with ``context``."""
        try:
            template = self.environment.from_string(source)
            result: str = template.render(**context)
            return result
        except Exception as exc:  # noqa: BLE001 - jinja2 raises many subclasses.
            raise TemplateRenderError(
                f"jinja2 render error: {exc}" + (f" in {filename}" if filename else "")
            ) from exc

    def render_file(self, src: Path, dst: Path, context: dict[str, Any]) -> None:
        """Read ``src``, render it, and write the result to ``dst``."""
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            try:
                text = src.read_text(encoding="utf-8")
            except UnicodeDecodeError as exc:
                raise TemplateRenderError(f"Could not decode {src} as UTF-8: {exc}") from exc
            safe_write_text(dst, self.render(text, context, filename=str(src)))
        except OSError as exc:
            raise TemplateRenderError(f"Could not render {src} to {dst}: {exc}") from exc


def jinja2_engine() -> Jinja2Engine:
    """Build a default :class:`Jinja2Engine`.

    Raises :class:`TemplateRenderError` with an install hint if jinja2 is not
    installed.
    """
    try:
        import jinja2 as _jinja2  # noqa: PLC0415 - optional extra import.
    except ImportError as exc:  # pragma: no cover - exercised only without extra.
        raise TemplateRenderError(
            "jinja2 template engine requires the 'jinja2' extra. "
            "Install it with: pip install behave-gen[jinja2]"
        ) from exc
    env = _jinja2.Environment(
        keep_trailing_newline=True,
        undefined=_jinja2.StrictUndefined,
        autoescape=False,  # nosec B701 # noqa: S701 - templates generate source files, not HTML.
    )
    return Jinja2Engine(environment=env)


def get_engine(name: str) -> TemplateEngine:
    """Return a template engine by name.

    Args:
        name: ``"string"`` or ``"jinja2"``.

    Raises:
        ValueError: If ``name`` is not a recognised engine.
        TemplateRenderError: If ``jinja2`` is requested but not installed.

    """
    if name == "string":
        return StringTemplateEngine()
    if name == "jinja2":
        return jinja2_engine()
    raise ValueError(f"Unknown template engine {name!r}. Valid values: 'string', 'jinja2'.")
