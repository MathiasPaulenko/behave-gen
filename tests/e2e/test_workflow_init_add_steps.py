"""E2E: ``init`` → ``add feature`` → ``add steps`` → ``behave --dry-run``.

Verifies that a project generated from scratch with features and step
libraries is structurally valid and passes ``behave --dry-run``.
"""

from __future__ import annotations

from pathlib import Path

from behave_gen.commands.add import AddFeatureOptions, add_feature
from behave_gen.commands.environment import AddEnvironmentOptions, add_environment
from behave_gen.commands.steps import AddStepsOptions, add_steps

from .conftest import collect_files, parse_all_features, run_behave_dry_run, run_ruff_check


class TestInitScaffolding:
    """The ``init`` command produces a complete, valid project skeleton."""

    def test_init_creates_expected_files(self, project: Path) -> None:
        files = collect_files(project)
        assert "features/.gitkeep" in files
        assert "features/steps/.gitkeep" in files
        assert "environment.py" in files
        assert "behave.toml" in files
        assert "pyproject.toml" in files
        assert "README.md" in files

    def test_init_project_name_in_pyproject(self, project: Path) -> None:
        pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
        assert 'name = "e2e_proj"' in pyproject

    def test_init_project_name_in_readme(self, project: Path) -> None:
        readme = (project / "README.md").read_text(encoding="utf-8")
        assert "# e2e_proj" in readme

    def test_init_passes_behave_dry_run(self, project: Path) -> None:
        proc = run_behave_dry_run(project)
        assert proc.returncode == 0, f"behave --dry-run failed:\n{proc.stdout}\n{proc.stderr}"

    def test_init_environment_passes_ruff(self, project: Path) -> None:
        proc = run_ruff_check(project, "environment.py")
        assert proc.returncode == 0, f"ruff failed:\n{proc.stdout}\n{proc.stderr}"


class TestAddFeature:
    """``add feature`` generates parseable ``.feature`` files.

    The ``init`` command creates a ``sample.feature`` placeholder, so every
    project starts with 1 feature. Adding features increases the count.
    """

    def test_default_template_parses(self, project: Path) -> None:
        add_feature(project, AddFeatureOptions(name="login"))
        features = parse_all_features(project / "features")
        # sample.feature (from init) + login.feature
        assert len(features) == 2
        login = next(f for f in features if f.name == "Login")
        assert login is not None

    def test_crud_template_parses(self, project: Path) -> None:
        add_feature(project, AddFeatureOptions(name="checkout", template="crud"))
        features = parse_all_features(project / "features")
        assert len(features) == 2
        checkout = next(f for f in features if f.name == "Checkout")
        assert checkout is not None

    def test_tags_appear_in_feature(self, project: Path) -> None:
        add_feature(project, AddFeatureOptions(name="login", tags="smoke,auth"))
        content = (project / "features" / "login.feature").read_text(encoding="utf-8")
        assert "@smoke" in content
        assert "@auth" in content

    def test_multiple_features(self, project: Path) -> None:
        add_feature(project, AddFeatureOptions(name="login"))
        add_feature(project, AddFeatureOptions(name="checkout", template="crud"))
        add_feature(project, AddFeatureOptions(name="search"))
        features = parse_all_features(project / "features")
        # sample.feature + login + checkout + search
        assert len(features) == 4


class TestAddSteps:
    """``add steps`` generates real, importable step libraries."""

    def test_http_steps_created(self, project: Path) -> None:
        path = add_steps(project, AddStepsOptions(lib="http"))
        assert path == (project / "features" / "steps" / "http_steps.py").resolve()
        assert path.is_file()
        content = path.read_text(encoding="utf-8")
        assert "from behave import given, then, when" in content
        assert "BASE_URL" in content

    def test_auth_steps_created(self, project: Path) -> None:
        path = add_steps(project, AddStepsOptions(lib="auth"))
        assert path == (project / "features" / "steps" / "auth_steps.py").resolve()
        content = path.read_text(encoding="utf-8")
        assert "from behave import given, then, when" in content

    def test_http_steps_pass_ruff(self, project: Path) -> None:
        add_steps(project, AddStepsOptions(lib="http"))
        proc = run_ruff_check(project, "features/steps/http_steps.py")
        assert proc.returncode == 0, f"ruff failed:\n{proc.stdout}\n{proc.stderr}"

    def test_auth_steps_pass_ruff(self, project: Path) -> None:
        add_steps(project, AddStepsOptions(lib="auth"))
        proc = run_ruff_check(project, "features/steps/auth_steps.py")
        assert proc.returncode == 0, f"ruff failed:\n{proc.stdout}\n{proc.stderr}"


class TestFullWorkflowBehaveDryRun:
    """A project with features + steps passes ``behave --dry-run``.

    The placeholder features from ``add feature`` use generic step text that
    doesn't match any step library. For ``--dry-run`` to pass, we write
    features that use the actual HTTP step library patterns.
    """

    @staticmethod
    def _write_http_feature(root: Path) -> None:
        """Write a feature file that uses the HTTP step library patterns."""
        (root / "features" / "api.feature").write_text(
            "@api\n"
            "Feature: API\n"
            "  Scenario: List items\n"
            '    Given the base URL is "http://localhost:8080"\n'
            '    When I send a GET request to "/items"\n'
            "    Then the response status should be 200\n",
            encoding="utf-8",
        )

    def test_project_with_http_feature_and_steps(self, project: Path) -> None:
        add_steps(project, AddStepsOptions(lib="http"))
        self._write_http_feature(project)
        proc = run_behave_dry_run(project)
        assert proc.returncode == 0, f"behave --dry-run failed:\n{proc.stdout}\n{proc.stderr}"

    def test_project_with_auth_feature_and_steps(self, project: Path) -> None:
        add_steps(project, AddStepsOptions(lib="auth"))
        (project / "features" / "auth_test.feature").write_text(
            "Feature: Auth\n"
            "  Scenario: Not authenticated\n"
            "    Given I am not authenticated\n"
            "    Then I should not be authenticated\n",
            encoding="utf-8",
        )
        proc = run_behave_dry_run(project)
        assert proc.returncode == 0, f"behave --dry-run failed:\n{proc.stdout}\n{proc.stderr}"

    def test_project_with_kit_environment(self, project: Path) -> None:
        add_environment(project, AddEnvironmentOptions(kit=True))
        # A project with only sample.feature (no user features) should pass.
        proc = run_behave_dry_run(project)
        assert proc.returncode == 0, f"behave --dry-run failed:\n{proc.stdout}\n{proc.stderr}"
