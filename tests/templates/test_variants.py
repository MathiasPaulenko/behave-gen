"""Tests for environment template variant selection."""

from __future__ import annotations

import pytest

from behave_gen.templates.variants import build_skip_and_rename, environment_variant

_ENV = "environment.py"
_ENV_KIT = "environment_with_kit.py"
_ENV_DATA = "environment_with_data.py"
_ENV_KIT_DATA = "environment_with_kit_data.py"
_ALL_VARIANTS = frozenset({_ENV, _ENV_KIT, _ENV_DATA, _ENV_KIT_DATA})


@pytest.mark.parametrize(
    ("kit", "data", "expected"),
    [
        (False, False, _ENV),
        (True, False, _ENV_KIT),
        (False, True, _ENV_DATA),
        (True, True, _ENV_KIT_DATA),
    ],
)
def test_environment_variant(kit: bool, data: bool, expected: str) -> None:
    assert environment_variant(kit, data) == expected


@pytest.mark.parametrize(
    ("kit", "data", "expected_selected", "expected_rename"),
    [
        (False, False, _ENV, {}),
        (True, False, _ENV_KIT, {_ENV_KIT: _ENV}),
        (False, True, _ENV_DATA, {_ENV_DATA: _ENV}),
        (True, True, _ENV_KIT_DATA, {_ENV_KIT_DATA: _ENV}),
    ],
)
def test_build_skip_and_rename(
    kit: bool,
    data: bool,
    expected_selected: str,
    expected_rename: dict[str, str],
) -> None:
    skip, rename = build_skip_and_rename(kit, data)
    assert rename == expected_rename
    assert skip == _ALL_VARIANTS - {expected_selected}
