"""E2E: ``init`` → ``from-openapi`` → verify generated features and steps.

Verifies that features generated from an OpenAPI 3.x spec parse cleanly, the
HTTP step library is created when requested, and the generated project passes
``behave --dry-run``.
"""

from __future__ import annotations

from pathlib import Path

from behave_gen.commands.from_openapi import FromOpenApiOptions, run_from_openapi

from .conftest import parse_all_features, run_behave_dry_run, run_ruff_check


def test_outside_project_root_fails(project: Path, openapi_yaml_spec: Path, tmp_path: Path) -> None:
    rc = run_from_openapi(
        FromOpenApiOptions(spec=str(openapi_yaml_spec), out_dir=str(tmp_path)),
        project_root=project,
    )
    assert rc == 1


class TestFromOpenApiYaml:
    """``from-openapi`` with a YAML spec."""

    def test_generates_features(self, project: Path, openapi_yaml_spec: Path) -> None:
        rc = run_from_openapi(
            FromOpenApiOptions(
                spec=str(openapi_yaml_spec), out_dir="gen", step_lib="http", tag="api"
            ),
            project_root=project,
        )
        assert rc == 0
        gen = project / "gen" / "features"
        feature_files = list(gen.glob("*.feature"))
        assert len(feature_files) >= 1

    def test_generated_features_parse(self, project: Path, openapi_yaml_spec: Path) -> None:
        run_from_openapi(
            FromOpenApiOptions(
                spec=str(openapi_yaml_spec), out_dir="gen", step_lib="http", tag="api"
            ),
            project_root=project,
        )
        features = parse_all_features(project / "gen" / "features")
        assert len(features) >= 1
        for f in features:
            assert f.name

    def test_http_steps_generated(self, project: Path, openapi_yaml_spec: Path) -> None:
        run_from_openapi(
            FromOpenApiOptions(
                spec=str(openapi_yaml_spec), out_dir="gen", step_lib="http", tag="api"
            ),
            project_root=project,
        )
        steps_file = project / "gen" / "features" / "steps" / "http_steps.py"
        assert steps_file.is_file()
        content = steps_file.read_text(encoding="utf-8")
        assert "from behave import given, then, when" in content

    def test_tag_appears_in_features(self, project: Path, openapi_yaml_spec: Path) -> None:
        run_from_openapi(
            FromOpenApiOptions(
                spec=str(openapi_yaml_spec), out_dir="gen", step_lib="http", tag="api"
            ),
            project_root=project,
        )
        for path in (project / "gen" / "features").glob("*.feature"):
            content = path.read_text(encoding="utf-8")
            assert "@api" in content

    def test_generated_steps_pass_ruff(self, project: Path, openapi_yaml_spec: Path) -> None:
        run_from_openapi(
            FromOpenApiOptions(
                spec=str(openapi_yaml_spec), out_dir="gen", step_lib="http", tag="api"
            ),
            project_root=project,
        )
        proc = run_ruff_check(project, "gen/features/steps/http_steps.py")
        assert proc.returncode == 0, f"ruff failed:\n{proc.stdout}\n{proc.stderr}"


class TestFromOpenApiJson:
    """``from-openapi`` with a JSON spec."""

    def test_generates_features(self, project: Path, openapi_json_spec: Path) -> None:
        rc = run_from_openapi(
            FromOpenApiOptions(spec=str(openapi_json_spec), out_dir="gen", step_lib="http"),
            project_root=project,
        )
        assert rc == 0
        feature_files = list((project / "gen" / "features").glob("*.feature"))
        assert len(feature_files) >= 1


class TestFromOpenApiBehaveDryRun:
    """Generated OpenAPI features pass ``behave --dry-run``."""

    def test_dry_run_with_generated_steps(self, project: Path, openapi_yaml_spec: Path) -> None:
        run_from_openapi(
            FromOpenApiOptions(
                spec=str(openapi_yaml_spec), out_dir="gen", step_lib="http", tag="api"
            ),
            project_root=project,
        )
        proc = run_behave_dry_run(project / "gen")
        assert proc.returncode == 0, f"behave --dry-run failed:\n{proc.stdout}\n{proc.stderr}"
