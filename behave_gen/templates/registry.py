"""Registry of built-in and custom template sets for behave-gen.

Built-in template sets ship inside the package under
``behave_gen/templates/<name>``. Custom sets can be registered at runtime from
arbitrary directories.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path

from behave_gen.templates.discovery import TemplateSet

_BUILTIN_ROOT = "behave_gen.templates"


class TemplateRegistry:
    """Registry mapping template-set names to :class:`TemplateSet` instances."""

    def __init__(self) -> None:
        self._sets: dict[str, TemplateSet] = {}

    def register(self, template_set: TemplateSet) -> None:
        """Register a :class:`TemplateSet` by its name."""
        self._sets[template_set.name] = template_set

    def register_directory(self, root: str | Path, name: str | None = None) -> TemplateSet:
        """Register a template set from a directory."""
        template_set = TemplateSet.from_directory(root, name=name)
        self.register(template_set)
        return template_set

    def get(self, name: str) -> TemplateSet:
        """Return the registered template set for ``name``.

        Raises:
            KeyError: If the name is not registered, with the available names.
        """
        try:
            return self._sets[name]
        except KeyError:
            available = ", ".join(sorted(self._sets)) or "(none)"
            raise KeyError(f"Unknown template set {name!r}. Available: {available}.") from None

    def names(self) -> tuple[str, ...]:
        """Return the registered template-set names, sorted."""
        return tuple(sorted(self._sets))

    def has(self, name: str) -> bool:
        """Return True if ``name`` is registered."""
        return name in self._sets


def _builtin_path(name: str) -> Path:
    """Return the on-disk path to a built-in template set."""
    with resources.as_file(resources.files(_BUILTIN_ROOT).joinpath(name)) as p:
        return Path(p)


def default_registry() -> TemplateRegistry:
    """Build a registry pre-loaded with built-in template sets."""
    registry = TemplateRegistry()
    registry.register_directory(_builtin_path("default"), name="default")
    return registry
