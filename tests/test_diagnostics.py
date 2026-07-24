"""Tests for optional dependency diagnostics."""

from __future__ import annotations

from behave_gen.diagnostics import check_extra, install_hint, is_available


def test_check_extra_known_installed_extra() -> None:
    status = check_extra("doctor")
    assert status.name == "doctor"
    assert status.available is True
    assert status.install_hint == ""


def test_check_extra_unknown_extra() -> None:
    status = check_extra("nonexistent-extra")
    assert status.available is False
    assert "Unknown extra" in status.install_hint


def test_is_available_returns_bool() -> None:
    assert is_available("doctor") is True
    assert is_available("nonexistent-extra") is False


def test_install_hint_known_extra_is_empty() -> None:
    assert install_hint("doctor") == ""


def test_install_hint_unknown_extra_lists_known_extras() -> None:
    hint = install_hint("nonexistent-extra")
    assert "Unknown extra" in hint
    assert "doctor" in hint
