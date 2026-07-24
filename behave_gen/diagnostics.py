"""Optional-dependency handling for behave-gen integrations.

Centralises the "is this extra installed?" checks and install hints so command
modules stay thin and consistent.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["DependencyStatus", "check_extra", "install_hint", "is_available"]

EXTRAS: dict[str, str] = {
    "doctor": "behave_doctor",
    "lint": "behave_lint",
    "format": "behave_format",
    "kit": "behave_kit",
    "data": "behave_data",
    "jinja2": "jinja2",
    "openapi": "yaml",
    "swagger": "yaml",
}


@dataclass(frozen=True, slots=True)
class DependencyStatus:
    """Result of an optional-dependency availability check."""

    name: str
    available: bool
    install_hint: str


def check_extra(extra: str) -> DependencyStatus:
    """Return the availability status for an optional extra.

    Args:
        extra: Extra name (e.g. ``"doctor"``).

    Returns:
        A :class:`DependencyStatus` with an install hint when missing.
    """
    if extra not in EXTRAS:
        return DependencyStatus(
            name=extra,
            available=False,
            install_hint=f"Unknown extra {extra!r}. Known extras: {', '.join(sorted(EXTRAS))}.",
        )
    package = EXTRAS[extra]
    try:
        __import__(package.replace("-", "_"))
    except ImportError:
        return DependencyStatus(
            name=extra,
            available=False,
            install_hint=f"pip install behave-gen[{extra}]",
        )
    return DependencyStatus(name=extra, available=True, install_hint="")


def is_available(extra: str) -> bool:
    """Return True if the optional extra is importable."""
    return check_extra(extra).available


def install_hint(extra: str) -> str:
    """Return the install hint for an optional extra."""
    return check_extra(extra).install_hint
