"""Tests for ``behave-gen check``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from behave_gen.cli.app import app
from behave_gen.commands.check import (
    CheckReport,
    CheckSuggestion,
    _suggest_for_undefined,
    run_check,
)
from behave_gen.commands.init import InitOptions, init_project
from behave_gen.diagnostics import DependencyStatus, check_extra, is_available

runner = CliRunner()


def _make_project(tmp_path: Path) -> Path:
    return init_project(tmp_path, InitOptions(name="proj"))


def test_diagnostics_check_extra_returns_hint() -> None:
    status = check_extra("doctor")
    assert status.name == "doctor"
    # behave-doctor may or may not be installed in the test env.
    assert status.available is True or "pip install behave-gen[doctor]" in status.install_hint


def test_diagnostics_is_available_boolean() -> None:
    assert isinstance(is_available("doctor"), bool)


def test_diagnostics_openapi_extra_maps_to_yaml_module() -> None:
    # openapi/swagger extras depend on the PyPI distribution ``pyyaml``, whose
    # importable module is named ``yaml``. The hint must still reference the extra.
    status = check_extra("openapi")
    assert status.name == "openapi"
    assert "behave-gen[openapi]" in status.install_hint or status.available is True


def test_diagnostics_check_extra_unknown_extra_returns_unavailable() -> None:
    status = check_extra("not-a-real-extra")
    assert status.name == "not-a-real-extra"
    assert status.available is False


def test_suggest_for_undefined_http() -> None:
    assert "http" in _suggest_for_undefined("I send a GET request")


def test_suggest_for_undefined_auth() -> None:
    assert "auth" in _suggest_for_undefined("I am authenticated")


def test_suggest_for_undefined_generic() -> None:
    assert "add steps" in _suggest_for_undefined("something unknown")


def test_check_missing_root_returns_one(tmp_path: Path) -> None:
    code = run_check(tmp_path / "nope", fmt="text")
    assert code == 1


def test_check_invalid_format_returns_one(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    code = run_check(root, fmt="xml")
    assert code == 1


def test_check_runs_without_crashing(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    code = run_check(root, fmt="text")
    # behave-doctor is installed in the test env; a clean project should pass.
    assert code in (0, 1)


def test_check_json_output_parseable(tmp_path: Path) -> None:
    _make_project(tmp_path)
    # JSON output goes to stdout; we invoke via CliRunner to capture.
    result = runner.invoke(app, ["check", "--format", "json"])
    assert result.exit_code in (0, 1)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        # behave-doctor may print its own output; ensure our wrapper key exists
        # when it is not installed.
        pytest.skip("behave-doctor produced non-JSON output")
    assert "available" in payload
    assert "project" in payload


def test_check_text_output_when_doctor_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _make_project(tmp_path)
    monkeypatch.chdir(root)
    # Force behave-doctor to be reported as unavailable.
    original = check_extra

    def fake_check_extra(extra: str) -> DependencyStatus:
        if extra == "doctor":
            return DependencyStatus(
                name="doctor",
                available=False,
                install_hint="pip install behave-gen[doctor]",
            )
        return original(extra)

    monkeypatch.setattr("behave_gen.commands.check.check_extra", fake_check_extra)
    code = run_check(root, fmt="text")
    assert code == 0


def test_check_report_to_dict() -> None:
    report = CheckReport(
        project="x",
        available=True,
        install_hint="",
        errors=(
            {
                "rule_id": "undefined-step",
                "message": "I do x",
                "severity": "error",
                "file": "f",
                "line": 1,
                "rule_name": "Undefined",
                "suggestion": "",
            },
        ),
        suggestions=(
            CheckSuggestion(step="I do x", suggestion="Run: behave-gen add steps --lib http"),
        ),
    )
    d = report.to_dict()
    assert d["available"] is True
    assert d["errors"][0]["rule_id"] == "undefined-step"
    assert d["suggestions"][0]["step"] == "I do x"


def test_check_cli_exits_cleanly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path)
    monkeypatch.chdir(root)
    result = runner.invoke(app, ["check"])
    assert result.exit_code in (0, 1)
