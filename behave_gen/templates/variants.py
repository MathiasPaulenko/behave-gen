"""Shared environment template variants for behave-gen.

The default project template ships several ``environment.py`` variants. This
module centralizes the mapping so scaffolding and update commands stay in sync.
"""

from __future__ import annotations

# environment.py variants selected by the --kit / --data flags.
_ENVIRONMENT_VARIANTS = {
    (False, False): "environment.py",
    (True, False): "environment_with_kit.py",
    (False, True): "environment_with_data.py",
    (True, True): "environment_with_kit_data.py",
}

_ALL_ENVIRONMENT_VARIANTS = frozenset(_ENVIRONMENT_VARIANTS.values())


def environment_variant(kit: bool, data: bool) -> str:
    """Return the environment template filename for the given flags."""
    return _ENVIRONMENT_VARIANTS[(kit, data)]


def build_skip_and_rename(kit: bool, data: bool) -> tuple[frozenset[str], dict[str, str]]:
    """Compute which environment variants to skip and which to rename."""
    selected = environment_variant(kit, data)
    skip: set[str] = set()
    rename: dict[str, str] = {}
    for variant in _ALL_ENVIRONMENT_VARIANTS:
        if variant == "environment.py":
            if selected != "environment.py":
                skip.add(variant)
            continue
        if variant == selected:
            rename[variant] = "environment.py"
        else:
            skip.add(variant)
    return frozenset(skip), rename
