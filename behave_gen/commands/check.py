"""``behave-gen check`` command implementation.

Delegates to ``behave-doctor`` when installed and prints actionable
suggestions for undefined steps. Degrades to an install hint when the optional
``doctor`` extra is missing.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from behave_gen.config import BehaveGenConfig
from behave_gen.diagnostics import check_extra
from behave_gen.paths import resolve_project_root
from behave_gen.project import Project, ProjectError

_UNDEFINED_STEP_RULES = frozenset({"undefined-step", "undefined_step", "missing-step"})


class CheckError(Exception):
    """User-facing error raised by ``check``."""


@dataclass(frozen=True, slots=True)
class CheckSuggestion:
    """A suggestion for resolving an undefined step."""

    step: str
    suggestion: str


@dataclass(frozen=True, slots=True)
class CheckReport:
    """Structured result of a check run."""

    project: str
    available: bool
    install_hint: str
    errors: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    warnings: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    suggestions: tuple[CheckSuggestion, ...] = field(default_factory=tuple)
    exit_code: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dictionary representation."""
        return {
            "project": self.project,
            "available": self.available,
            "install_hint": self.install_hint,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "suggestions": [asdict(s) for s in self.suggestions],
            "exit_code": self.exit_code,
        }


def _to_int_line(value: object) -> int:
    """Convert a behave-doctor line value to a safe integer, defaulting to 0."""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return 0
    return 0


def _suggest_for_undefined(step_text: str) -> str:
    """Build a suggestion for an undefined step based on its text."""
    lowered = step_text.lower()
    if any(word in lowered for word in ("send", "request", "response", "get", "post", "http")):
        return "Run: behave-gen add steps --lib http"
    if any(word in lowered for word in ("session", "login", "token", "auth", "authenticated")):
        return "Run: behave-gen add steps --lib auth"
    return "Run: behave-gen add steps --lib <http|auth> or write a custom step."


def _build_report_from_doctor(project_root: Path, raw_report: Any) -> CheckReport:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    suggestions: list[CheckSuggestion] = []

    for diag in getattr(raw_report, "errors", []) or []:
        entry = {
            "rule_id": getattr(diag, "rule_id", ""),
            "rule_name": getattr(diag, "rule_name", ""),
            "severity": str(getattr(diag, "severity", "")),
            "message": getattr(diag, "message", ""),
            "file": str(getattr(diag, "file", "")),
            "line": _to_int_line(getattr(diag, "line", 0)),
            "suggestion": getattr(diag, "suggestion", ""),
        }
        errors.append(entry)
        rule_id = str(entry["rule_id"])
        message = str(entry["message"])
        if rule_id in _UNDEFINED_STEP_RULES or "undefined" in message.lower():
            suggestions.append(
                CheckSuggestion(step=message, suggestion=_suggest_for_undefined(message))
            )

    for diag in getattr(raw_report, "warnings", []) or []:
        warnings.append(
            {
                "rule_id": getattr(diag, "rule_id", ""),
                "message": getattr(diag, "message", ""),
                "file": str(getattr(diag, "file", "")),
            }
        )

    exit_code = int(getattr(raw_report, "exit_code", 0))
    return CheckReport(
        project=str(project_root),
        available=True,
        install_hint="",
        errors=tuple(errors),
        warnings=tuple(warnings),
        suggestions=tuple(suggestions),
        exit_code=exit_code,
    )


def run_check(
    project_root: str | Path | None = None,
    *,
    fmt: str = "text",
    config: BehaveGenConfig | None = None,
) -> int:
    """CLI entry point for ``behave-gen check``.

    Returns the exit code: ``0`` when behave-doctor is missing (graceful) or
    when the report has no errors; otherwise the doctor report's exit code.
    """
    root = resolve_project_root(project_root)
    try:
        project = Project.from_root(root, config=config)
    except ProjectError as exc:
        print(f"check: {exc}", file=sys.stderr)
        return 1

    fmt_normalized = fmt.lower()
    if fmt_normalized not in {"text", "json"}:
        print(f"check: Invalid format {fmt!r}. Use 'text' or 'json'.", file=sys.stderr)
        return 1

    status = check_extra("doctor")
    if not status.available:
        report = CheckReport(
            project=str(project.root),
            available=False,
            install_hint=status.install_hint,
        )
        _emit(report, fmt_normalized)
        return 0

    import behave_doctor  # noqa: PLC0415 - optional extra imported lazily.

    try:
        raw = behave_doctor.scan_project(project.root)
    except Exception as exc:  # noqa: BLE001 - surface doctor failures cleanly.
        print(f"check: behave-doctor failed: {exc}", file=sys.stderr)
        return 1

    report = _build_report_from_doctor(project.root, raw)
    _emit(report, fmt_normalized)
    return report.exit_code


def _emit(report: CheckReport, fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return
    if not report.available:
        print(f"behave-doctor is not installed. Install it with: {report.install_hint}")
        return
    print(f"Project: {report.project}")
    if report.errors:
        print(f"\nErrors ({len(report.errors)}):")
        for err in report.errors:
            print(f"  [{err['severity']}] {err['rule_name']}: {err['message']}")
            if err["file"]:
                print(f"    at {err['file']}:{err['line']}")
    else:
        print("\nNo errors found.")
    if report.warnings:
        print(f"\nWarnings ({len(report.warnings)}):")
        for warn in report.warnings:
            print(f"  {warn['rule_id']}: {warn['message']}")
    if report.suggestions:
        print("\nSuggestions:")
        for sug in report.suggestions:
            print(f"  - {sug.suggestion}")
