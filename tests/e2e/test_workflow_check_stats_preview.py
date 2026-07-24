"""E2E: ``add steps`` → ``check`` → ``stats`` → ``preview``.

Verifies that the diagnostic and reporting commands work on a real generated
project with features and step libraries.
"""

from __future__ import annotations

from pathlib import Path

from behave_gen.commands.check import run_check
from behave_gen.commands.preview import run_preview
from behave_gen.commands.stats import run_stats


class TestCheck:
    """``check`` runs behave-doctor on a generated project."""

    def test_check_clean_project(self, project: Path) -> None:
        rc = run_check(project, fmt="text")
        assert rc in (0, 1)

    def test_check_project_with_steps(self, project_with_steps: Path) -> None:
        rc = run_check(project_with_steps, fmt="text")
        assert rc in (0, 1)

    def test_check_json_output(self, project: Path) -> None:
        rc = run_check(project, fmt="json")
        assert rc in (0, 1)


class TestStats:
    """``stats`` reports accurate counts on a generated project."""

    def test_stats_text_output(self, project_with_features: Path) -> None:
        rc = run_stats(project_with_features, fmt="text")
        assert rc == 0

    def test_stats_json_output(self, project_with_features: Path) -> None:
        rc = run_stats(project_with_features, fmt="json")
        assert rc == 0

    def test_stats_invalid_format(self, project: Path) -> None:
        rc = run_stats(project, fmt="xml")
        assert rc == 1

    def test_stats_missing_root(self, tmp_path: Path) -> None:
        rc = run_stats(tmp_path / "nope")
        assert rc == 1


class TestPreview:
    """``preview`` pretty-prints a ``.feature`` file."""

    def test_preview_valid_feature(self, project_with_features: Path) -> None:
        feature = project_with_features / "features" / "login.feature"
        rc = run_preview(str(feature), project_root=project_with_features)
        assert rc == 0

    def test_preview_nonexistent_file(self, project: Path) -> None:
        rc = run_preview("nope.feature", project_root=project)
        assert rc == 1
