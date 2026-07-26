"""Tests for path helpers."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from behave_gen.paths import is_windows_reserved_name, safe_write_text, validate_name


def test_validate_name_accepts_simple_name() -> None:
    assert validate_name("my_feature") == "my_feature"


def test_validate_name_strips_whitespace() -> None:
    assert validate_name("  my_feature  ") == "my_feature"


def test_validate_name_rejects_empty() -> None:
    with pytest.raises(ValueError, match="empty"):
        validate_name("   ")


def test_validate_name_rejects_dot_names() -> None:
    for name in (".", "..", "...", "...."):
        with pytest.raises(ValueError, match="dots"):
            validate_name(name)


def test_validate_name_rejects_path_separators() -> None:
    with pytest.raises(ValueError, match="forbidden"):
        validate_name("a/b")
    with pytest.raises(ValueError, match="forbidden"):
        validate_name("a\\b")


def test_validate_name_rejects_absolute_path() -> None:
    with pytest.raises(ValueError, match="absolute"):
        validate_name("C:\\project")


def test_validate_name_rejects_control_characters() -> None:
    with pytest.raises(ValueError, match="control"):
        validate_name("my\x01feature")


def test_validate_name_strips_trailing_whitespace() -> None:
    assert validate_name("feature ") == "feature"


def test_validate_name_rejects_trailing_period() -> None:
    with pytest.raises(ValueError, match="end with"):
        validate_name("feature.")


@pytest.mark.skipif(sys.platform != "win32", reason="Windows reserved name check")
def test_validate_name_rejects_windows_reserved_names() -> None:
    for name in (
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "LPT1",
        "CON.txt",
        "COM5.log",
        "COM1.tar.gz",
        "LPT9.old.log",
    ):
        with pytest.raises(ValueError, match="reserved"):
            validate_name(name)


def test_safe_write_text_uses_lf_line_endings(tmp_path: Path) -> None:
    target = tmp_path / "out.txt"
    safe_write_text(target, "line1\nline2\n")
    assert target.read_bytes() == b"line1\nline2\n"


def test_is_windows_reserved_name_detects_reserved_names(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reserved names and their dotted variants are detected on Windows."""
    monkeypatch.setattr("sys.platform", "win32")
    assert is_windows_reserved_name("CON")
    assert is_windows_reserved_name("COM1")
    assert is_windows_reserved_name("COM1.tar.gz")
    assert not is_windows_reserved_name("my_feature")
