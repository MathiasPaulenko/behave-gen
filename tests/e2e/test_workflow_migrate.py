"""E2E: ``init`` → ``migrate`` → verify migrated Cucumber features.

Verifies that Cucumber (Java) feature files are migrated into a Behave layout,
the migrated features parse cleanly, and the project structure is correct.
"""

from __future__ import annotations

from pathlib import Path

from behave_gen.commands.migrate import MigrateOptions, run_migrate

from .conftest import parse_all_features


class TestMigrateCucumber:
    """``migrate`` copies Cucumber features into a Behave layout."""

    def test_migrate_returns_zero(self, project: Path, cucumber_project: Path) -> None:
        rc = run_migrate(
            MigrateOptions(source=str(cucumber_project), out_dir="migrated"),
            project_root=project,
        )
        assert rc == 0

    def test_migrated_features_exist(self, project: Path, cucumber_project: Path) -> None:
        run_migrate(
            MigrateOptions(source=str(cucumber_project), out_dir="migrated"),
            project_root=project,
        )
        migrated = project / "migrated" / "features"
        feature_files = list(migrated.rglob("*.feature"))
        assert len(feature_files) == 2

    def test_migrated_features_parse(self, project: Path, cucumber_project: Path) -> None:
        run_migrate(
            MigrateOptions(source=str(cucumber_project), out_dir="migrated"),
            project_root=project,
        )
        features = parse_all_features(project / "migrated" / "features")
        assert len(features) == 2
        names = {f.name for f in features}
        assert "Login" in names
        assert "Checkout" in names

    def test_migrate_nonexistent_source_returns_one(self, project: Path) -> None:
        rc = run_migrate(
            MigrateOptions(source="does/not/exist", out_dir="migrated"),
            project_root=project,
        )
        assert rc == 1
