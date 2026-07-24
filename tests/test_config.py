"""Tests for behave_gen.config."""

from __future__ import annotations

from pathlib import Path

import pytest

from behave_gen.config import BehaveGenConfig, load_config


def test_default_config_is_frozen() -> None:
    config = BehaveGenConfig.default()
    with pytest.raises(AttributeError):  # FrozenInstanceError subclasses it.
        config.features_dir = "other"  # type: ignore[misc]


def test_default_config_values() -> None:
    config = BehaveGenConfig.default()
    assert config.features_dir == "features"
    assert config.steps_dir == "features/steps"
    assert config.environment_file == "environment.py"
    assert config.template_engine == "string"
    assert config.default_tags == ()


def test_load_config_missing_root_raises(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"
    with pytest.raises(FileNotFoundError):
        load_config(missing)


def test_load_config_no_pyproject_returns_default(tmp_path: Path) -> None:
    config = load_config(tmp_path)
    assert config == BehaveGenConfig.default()


def test_load_config_no_table_returns_default(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "demo"\n', encoding="utf-8")
    config = load_config(tmp_path)
    assert config == BehaveGenConfig.default()


def test_load_config_reads_known_keys(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[tool.behave-gen]\n"
        'features_dir = "specs"\n'
        'template_engine = "jinja2"\n'
        'default_tags = ["@smoke", "@api"]\n',
        encoding="utf-8",
    )
    config = load_config(tmp_path)
    assert config.features_dir == "specs"
    assert config.template_engine == "jinja2"
    assert config.default_tags == ("@smoke", "@api")


def test_load_config_unknown_key_raises(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.behave-gen]\nunknown_key = "value"\n', encoding="utf-8"
    )
    with pytest.raises(ValueError, match="Unknown"):
        load_config(tmp_path)


def test_load_config_invalid_template_engine_raises(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.behave-gen]\ntemplate_engine = "mako"\n', encoding="utf-8"
    )
    with pytest.raises(ValueError, match="Invalid template_engine"):
        load_config(tmp_path)


def test_with_overrides_rejects_unknown_keys() -> None:
    with pytest.raises(ValueError, match="Unknown config keys"):
        BehaveGenConfig.default().with_overrides(bogus="x")


def test_as_dict_roundtrip() -> None:
    config = BehaveGenConfig.default()
    restored = BehaveGenConfig(**config.as_dict())
    assert restored == config
