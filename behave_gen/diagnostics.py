"""Optional-dependency handling for behave-gen integrations.

Centralises the "is this extra installed?" checks and install hints so command
modules stay thin and consistent.
"""

from __future__ import annotations

from dataclasses import dataclass

EXTRAS: dict[str, str] = {
    "doctor": "behave-doctor",
    "lint": "behave-lint",
    "format": "behave-format",
    "kit": "behave-kit",
    "data": "behave-data",
    "jinja2": "jinja2",
    "openapi": "pyyaml",
    "swagger": "pyyaml",
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
    package = EXTRAS.get(extra, extra)
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
