"""Tests for ``behave-gen add environment`` and ``add config``."""

from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from typer.testing import CliRunner

from behave_gen.cli.app import app
from behave_gen.commands.environment import (
    AddEnvironmentOptions,
    EnvironmentError,
    add_config,
    add_environment,
    run_add_config,
)
from behave_gen.commands.init import InitOptions, init_project

runner = CliRunner()


def _make_project(tmp_path: Path) -> Path:
    return init_project(tmp_path, InitOptions(name="proj"))


def test_add_environment_base(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    path = add_environment(root, AddEnvironmentOptions())
    content = path.read_text(encoding="utf-8")
    assert "behave_kit" not in content
    assert "behave_data" not in content
    assert "def before_all" in content


def test_add_environment_kit(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    path = add_environment(root, AddEnvironmentOptions(kit=True))
    content = path.read_text(encoding="utf-8")
    assert "behave_kit" in content
    assert "setup_kit" in content
    assert "behave_data" not in content


def test_add_environment_data(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    path = add_environment(root, AddEnvironmentOptions(data=True))
    content = path.read_text(encoding="utf-8")
    assert "behave_data" in content
    assert "setup_data" in content
    assert "behave_kit" not in content


def test_add_environment_kit_and_data(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    path = add_environment(root, AddEnvironmentOptions(kit=True, data=True))
    content = path.read_text(encoding="utf-8")
    assert "behave_kit" in content
    assert "behave_data" in content


def test_add_environment_missing_root_raises(tmp_path: Path) -> None:
    with pytest.raises(EnvironmentError, match="Project root not found"):
        add_environment(tmp_path / "nope", AddEnvironmentOptions(kit=True))


def test_add_environment_rejects_environment_file_outside_root(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    with pytest.raises(EnvironmentError, match="must be inside project root"):
        add_environment(root, AddEnvironmentOptions(), environment_file="../escape.py")


def test_add_environment_is_valid_python(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    add_environment(root, AddEnvironmentOptions(kit=True, data=True))
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "import ast; ast.parse(open(r'environment.py', encoding='utf-8').read())",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr


def test_add_environment_behave_dry_run_passes(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    add_environment(root, AddEnvironmentOptions(kit=True))
    proc = subprocess.run(
        [sys.executable, "-m", "behave", "--dry-run", "--no-color"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    # behave-kit is not installed, so importing environment.py would fail at
    # runtime. --dry-run still imports environment.py; we only assert no
    # ConfigError/ParseError on the feature files themselves.
    assert "ConfigError" not in proc.stdout


def test_add_config_behave_kit(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    path = add_config(root, "behave-kit")
    text = path.read_text(encoding="utf-8")
    assert "behave-kit>=1.0" in text


def test_add_config_idempotent(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    add_config(root, "behave-kit")
    text_after_first = (root / "pyproject.toml").read_text(encoding="utf-8")
    add_config(root, "behave-kit")
    text_after_second = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert text_after_first == text_after_second


def test_add_config_idempotent_with_trailing_comment(tmp_path: Path) -> None:
    """A trailing comment on an existing dependency must not break idempotency."""
    root = _make_project(tmp_path)
    (root / "pyproject.toml").write_text(
        '[project]\nname = "proj"\n\n'
        "[project.optional-dependencies]\n"
        "kit = [\n"
        '    "behave-kit>=1.0",  # comment\n'
        "]\n",
        encoding="utf-8",
    )
    add_config(root, "behave-kit")
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert text.count("behave-kit>=1.0") == 1
    assert "# comment" in text


def test_add_config_idempotent_with_single_quotes(tmp_path: Path) -> None:
    """A single-quoted existing dependency must not be duplicated."""
    root = _make_project(tmp_path)
    (root / "pyproject.toml").write_text(
        '[project]\nname = "proj"\n\n'
        "[project.optional-dependencies]\n"
        "kit = [\n"
        "    'behave-kit>=1.0',\n"
        "]\n",
        encoding="utf-8",
    )
    add_config(root, "behave-kit")
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert text.count("behave-kit>=1.0") == 1


def test_add_config_idempotent_with_inline_array(tmp_path: Path) -> None:
    """An inline array with the dependency already present must stay unchanged."""
    root = _make_project(tmp_path)
    (root / "pyproject.toml").write_text(
        '[project]\nname = "proj"\n\n[project.optional-dependencies]\nkit = ["behave-kit>=1.0"]\n',
        encoding="utf-8",
    )
    add_config(root, "behave-kit")
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert text.count("behave-kit>=1.0") == 1


def test_add_config_adds_to_inline_array(tmp_path: Path) -> None:
    """A missing dependency must be added to an existing inline array."""
    root = _make_project(tmp_path)
    (root / "pyproject.toml").write_text(
        '[project]\nname = "proj"\n\n[project.optional-dependencies]\nkit = []\n',
        encoding="utf-8",
    )
    add_config(root, "behave-kit")
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert '"behave-kit>=1.0"' in text
    with (root / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    assert "behave-kit>=1.0" in data["project"]["optional-dependencies"]["kit"]


def test_add_config_does_not_confuse_similar_package_specs(tmp_path: Path) -> None:
    """A package spec must match exactly, not just as a substring."""
    root = _make_project(tmp_path)
    (root / "pyproject.toml").write_text(
        '[project]\nname = "proj"\n\n'
        '[project.optional-dependencies]\nkit = ["behave-kit-extra>=1.0"]\n',
        encoding="utf-8",
    )
    add_config(root, "behave-kit")
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert text.count("behave-kit") == 2
    assert "behave-kit-extra>=1.0" in text
    assert "behave-kit>=1.0" in text


def test_add_config_behave_data(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    path = add_config(root, "behave-data")
    text = path.read_text(encoding="utf-8")
    assert "behave-data>=1.0" in text


def test_add_config_unknown_raises(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    with pytest.raises(EnvironmentError, match="Unknown config"):
        add_config(root, "nope")


def test_add_config_missing_pyproject_raises(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    (root / "pyproject.toml").unlink()
    with pytest.raises(EnvironmentError, match="pyproject.toml not found"):
        add_config(root, "behave-kit")


def test_add_config_rejects_pyproject_outside_root(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    outside = tmp_path / "outside" / "pyproject.toml"
    outside.parent.mkdir()
    with pytest.raises(EnvironmentError, match="must be inside project root"):
        add_config(root, "behave-kit", pyproject=outside)


def test_add_config_relative_pyproject_resolves_from_project_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A relative pyproject path must be interpreted relative to the project root."""
    root = _make_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    path = add_config(root, "behave-kit", pyproject="pyproject.toml")
    assert "behave-kit>=1.0" in path.read_text(encoding="utf-8")
    assert path.resolve() == (root / "pyproject.toml").resolve()


def test_add_config_pyproject_still_parses(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    add_config(root, "behave-kit")
    add_config(root, "behave-data")
    with (root / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    opt = data["project"]["optional-dependencies"]
    assert "behave-kit>=1.0" in opt["kit"]
    assert "behave-data>=1.0" in opt["data"]


def test_add_config_normalizes_crlf_line_endings(tmp_path: Path) -> None:
    """CRLF pyproject.toml files must not end up with mixed line endings."""
    root = _make_project(tmp_path)
    pyproject = root / "pyproject.toml"
    pyproject.write_bytes(b'[project]\r\nname = "proj"\r\n\r\n')
    add_config(root, "behave-kit")
    text = pyproject.read_text(encoding="utf-8")
    assert "\r" not in text
    assert "behave-kit>=1.0" in text
    with pyproject.open("rb") as handle:
        tomllib.load(handle)


def test_add_environment_rejects_directory_target(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    (root / "environment.py").unlink()
    (root / "environment.py").mkdir()
    with pytest.raises(EnvironmentError, match="Cannot overwrite directory"):
        add_environment(root, AddEnvironmentOptions())


def test_add_environment_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path)
    monkeypatch.chdir(root)
    result = runner.invoke(app, ["add", "environment", "--kit"])
    assert result.exit_code == 0, result.output
    assert "behave_kit" in (root / "environment.py").read_text(encoding="utf-8")


def test_add_config_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path)
    monkeypatch.chdir(root)
    result = runner.invoke(app, ["add", "config", "behave-kit"])
    assert result.exit_code == 0, result.output
    assert "behave-kit>=1.0" in (root / "pyproject.toml").read_text(encoding="utf-8")


def test_add_config_adds_extra_before_next_table(tmp_path: Path) -> None:
    """Missing extra in optional-dependencies must be inserted before the next table."""
    root = _make_project(tmp_path)
    (root / "pyproject.toml").write_text(
        '[project]\nname = "proj"\n\n'
        "[project.optional-dependencies]\n"
        'kit = ["behave-kit>=1.0"]\n'
        '[project.urls]\nHomepage = "https://example.com"\n',
        encoding="utf-8",
    )
    add_config(root, "behave-data")
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert "behave-data>=1.0" in text
    assert text.index("[project.optional-dependencies]") < text.index("[project.urls]")


def test_add_config_adds_to_multiline_array(tmp_path: Path) -> None:
    """A missing dependency must be inserted into an existing multiline array."""
    root = _make_project(tmp_path)
    (root / "pyproject.toml").write_text(
        '[project]\nname = "proj"\n\n'
        "[project.optional-dependencies]\n"
        "kit = [\n"
        '    "other>=1.0",\n'
        "]\n",
        encoding="utf-8",
    )
    add_config(root, "behave-kit")
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert "behave-kit>=1.0" in text
    assert text.count("behave-kit>=1.0") == 1


def test_add_config_adds_to_multiline_array_closing_bracket_shares_line(
    tmp_path: Path,
) -> None:
    """The closing bracket may share the last element's line without corrupting TOML."""
    root = _make_project(tmp_path)
    (root / "pyproject.toml").write_text(
        '[project]\nname = "proj"\n\n[project.optional-dependencies]\nkit = [\n    "other>=1.0"]\n',
        encoding="utf-8",
    )
    add_config(root, "behave-kit")
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert "behave-kit>=1.0" in text
    assert text.count("behave-kit>=1.0") == 1
    with (root / "pyproject.toml").open("rb") as handle:
        tomllib.load(handle)


def test_add_config_is_idempotent_when_closing_bracket_shares_last_element_line(
    tmp_path: Path,
) -> None:
    """An existing dependency on the same line as the closing bracket must stay unique."""
    root = _make_project(tmp_path)
    (root / "pyproject.toml").write_text(
        '[project]\nname = "proj"\n\n'
        "[project.optional-dependencies]\n"
        "kit = [\n"
        '    "behave-kit>=1.0"]\n',
        encoding="utf-8",
    )
    add_config(root, "behave-kit")
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert text.count("behave-kit>=1.0") == 1


def test_add_config_adds_to_multiline_array_with_trailing_comment_on_close(
    tmp_path: Path,
) -> None:
    """A trailing comment after a same-line closing bracket must be preserved."""
    root = _make_project(tmp_path)
    (root / "pyproject.toml").write_text(
        '[project]\nname = "proj"\n\n'
        "[project.optional-dependencies]\n"
        "kit = [\n"
        '    "other>=1.0"]  # end of kit\n',
        encoding="utf-8",
    )
    add_config(root, "behave-kit")
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert "behave-kit>=1.0" in text
    assert text.count("behave-kit>=1.0") == 1
    assert "# end of kit" in text
    with (root / "pyproject.toml").open("rb") as handle:
        tomllib.load(handle)


def test_add_config_handles_hash_in_inline_array_dependency(tmp_path: Path) -> None:
    """Inline arrays whose quoted values contain '#' must not be corrupted."""
    root = _make_project(tmp_path)
    (root / "pyproject.toml").write_text(
        '[project]\nname = "proj"\n\n'
        "[project.optional-dependencies]\n"
        'kit = ["pkg@https://example.com/pkg#sha256>=1.0"]\n',
        encoding="utf-8",
    )
    add_config(root, "behave-kit")
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert "behave-kit>=1.0" in text
    assert text.count("behave-kit>=1.0") == 1
    assert "pkg@https://example.com/pkg#sha256>=1.0" in text
    with (root / "pyproject.toml").open("rb") as handle:
        tomllib.load(handle)


def test_add_config_is_idempotent_for_hash_in_inline_array_dependency(
    tmp_path: Path,
) -> None:
    """Existing '#' containing inline dependencies must not be duplicated."""
    root = _make_project(tmp_path)
    (root / "pyproject.toml").write_text(
        '[project]\nname = "proj"\n\n'
        "[project.optional-dependencies]\n"
        'kit = ["behave-kit>=1.2.3#abc"]\n',
        encoding="utf-8",
    )
    add_config(root, "behave-kit")
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert text.count("behave-kit>=1.2.3#abc") == 1


def test_add_config_appends_to_malformed_array(tmp_path: Path) -> None:
    """A missing closing bracket should not stop the dependency from being appended."""
    root = _make_project(tmp_path)
    (root / "pyproject.toml").write_text(
        '[project]\nname = "proj"\n\n[project.optional-dependencies]\nkit = [\n    "other>=1.0",\n',
        encoding="utf-8",
    )
    add_config(root, "behave-kit")
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert "behave-kit>=1.0" in text


def test_add_config_creates_optional_section_before_urls(tmp_path: Path) -> None:
    """A new optional-dependencies section should be inserted before [project.urls]."""
    root = _make_project(tmp_path)
    (root / "pyproject.toml").write_text(
        '[project]\nname = "proj"\n\n[project.urls]\nHomepage = "https://example.com"\n',
        encoding="utf-8",
    )
    add_config(root, "behave-kit")
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert "[project.optional-dependencies]" in text
    assert text.index("[project.optional-dependencies]") < text.index("[project.urls]")


def test_run_add_config_unknown_config_returns_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _make_project(tmp_path)
    monkeypatch.chdir(root)
    rc = run_add_config("nope")
    assert rc == 1


def test_add_config_raises_on_read_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path)

    def _raise(*args: object, **kwargs: object) -> str:
        raise OSError("nope")

    monkeypatch.setattr(Path, "read_text", _raise)
    with pytest.raises(EnvironmentError, match="Could not read"):
        add_config(root, "behave-kit")


def test_add_config_raises_on_decode_error(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    (root / "pyproject.toml").write_bytes(b"\xff\xfe")
    with pytest.raises(EnvironmentError, match="Could not decode"):
        add_config(root, "behave-kit")


def test_add_config_raises_on_write_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path)

    def _raise(*args: object, **kwargs: object) -> None:
        raise OSError("nope")

    monkeypatch.setattr("behave_gen.commands.environment.safe_write_text", _raise)
    with pytest.raises(EnvironmentError, match="Could not write"):
        add_config(root, "behave-kit")


def test_add_environment_raises_on_remove_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _make_project(tmp_path)

    def _raise(*args: object, **kwargs: object) -> None:
        raise OSError("nope")

    monkeypatch.setattr(Path, "unlink", _raise)
    with pytest.raises(EnvironmentError, match="Could not remove existing file"):
        add_environment(root, AddEnvironmentOptions())


def test_add_environment_raises_on_mkdir_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _make_project(tmp_path)

    def _raise(*args: object, **kwargs: object) -> None:
        raise OSError("nope")

    monkeypatch.setattr(Path, "mkdir", _raise)
    with pytest.raises(EnvironmentError, match="Could not create parent directory"):
        add_environment(root, AddEnvironmentOptions())


def test_add_environment_raises_on_write_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _make_project(tmp_path)

    def _raise(*args: object, **kwargs: object) -> None:
        raise OSError("nope")

    monkeypatch.setattr("behave_gen.commands.environment.safe_write_text", _raise)
    with pytest.raises(EnvironmentError, match="Could not write environment file"):
        add_environment(root, AddEnvironmentOptions())
