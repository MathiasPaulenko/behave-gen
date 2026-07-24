"""E2E: ``from-postman`` and ``from-swagger`` generation.

Verifies that features generated from Postman collections and Swagger 2.0 specs
parse cleanly and the project structure is correct.
"""

from __future__ import annotations

from pathlib import Path

from behave_gen.commands.from_postman import FromPostmanOptions, run_from_postman
from behave_gen.commands.from_swagger import FromSwaggerOptions, run_from_swagger

from .conftest import parse_all_features, run_behave_dry_run, run_ruff_check


class TestFromPostman:
    """``from-postman`` generates features from a Postman Collection v2.1."""

    def test_generates_features(self, project: Path, postman_collection: Path) -> None:
        rc = run_from_postman(
            FromPostmanOptions(collection=str(postman_collection), out_dir="gen", tag="api"),
            project_root=project,
        )
        assert rc == 0
        feature_files = list((project / "gen" / "features").glob("*.feature"))
        assert len(feature_files) >= 1

    def test_generated_features_parse(self, project: Path, postman_collection: Path) -> None:
        run_from_postman(
            FromPostmanOptions(collection=str(postman_collection), out_dir="gen", tag="api"),
            project_root=project,
        )
        features = parse_all_features(project / "gen" / "features")
        assert len(features) >= 1

    def test_tag_appears_in_features(self, project: Path, postman_collection: Path) -> None:
        run_from_postman(
            FromPostmanOptions(collection=str(postman_collection), out_dir="gen", tag="api"),
            project_root=project,
        )
        for path in (project / "gen" / "features").glob("*.feature"):
            assert "@api" in path.read_text(encoding="utf-8")

    def test_http_steps_generated(self, project: Path, postman_collection: Path) -> None:
        run_from_postman(
            FromPostmanOptions(
                collection=str(postman_collection), out_dir="gen", step_lib="http", tag="api"
            ),
            project_root=project,
        )
        steps_file = project / "gen" / "features" / "steps" / "http_steps.py"
        assert steps_file.is_file()

    def test_invalid_collection_returns_one(self, project: Path) -> None:
        rc = run_from_postman(
            FromPostmanOptions(collection="nonexistent.json", out_dir="gen"),
            project_root=project,
        )
        assert rc == 1


class TestFromSwagger:
    """``from-swagger`` converts Swagger 2.0 to OpenAPI 3.x and generates features."""

    def test_generates_features(self, project: Path, swagger2_spec: Path) -> None:
        rc = run_from_swagger(
            FromSwaggerOptions(spec=str(swagger2_spec), out_dir="gen", step_lib="http", tag="api"),
            project_root=project,
        )
        assert rc == 0
        feature_files = list((project / "gen" / "features").glob("*.feature"))
        assert len(feature_files) >= 1

    def test_generated_features_parse(self, project: Path, swagger2_spec: Path) -> None:
        run_from_swagger(
            FromSwaggerOptions(spec=str(swagger2_spec), out_dir="gen", step_lib="http", tag="api"),
            project_root=project,
        )
        features = parse_all_features(project / "gen" / "features")
        assert len(features) >= 1

    def test_http_steps_generated(self, project: Path, swagger2_spec: Path) -> None:
        run_from_swagger(
            FromSwaggerOptions(spec=str(swagger2_spec), out_dir="gen", step_lib="http", tag="api"),
            project_root=project,
        )
        steps_file = project / "gen" / "features" / "steps" / "http_steps.py"
        assert steps_file.is_file()

    def test_generated_steps_pass_ruff(self, project: Path, swagger2_spec: Path) -> None:
        run_from_swagger(
            FromSwaggerOptions(spec=str(swagger2_spec), out_dir="gen", step_lib="http", tag="api"),
            project_root=project,
        )
        proc = run_ruff_check(project, "gen/features/steps/http_steps.py")
        assert proc.returncode == 0, f"ruff failed:\n{proc.stdout}\n{proc.stderr}"

    def test_dry_run_generated_project(self, project: Path, swagger2_spec: Path) -> None:
        run_from_swagger(
            FromSwaggerOptions(spec=str(swagger2_spec), out_dir="gen", step_lib="http", tag="api"),
            project_root=project,
        )
        proc = run_behave_dry_run(project / "gen")
        assert proc.returncode == 0, f"behave --dry-run failed:\n{proc.stdout}\n{proc.stderr}"
