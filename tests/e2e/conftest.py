"""Shared fixtures for end-to-end tests."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from behave_model import parse_feature as _parse_feature

from behave_gen.commands.add import AddFeatureOptions, add_feature
from behave_gen.commands.environment import AddEnvironmentOptions, add_environment
from behave_gen.commands.init import InitOptions, init_project
from behave_gen.commands.steps import AddStepsOptions, add_steps
from behave_gen.paths import safe_parse_feature_filename


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a bare Behave project and return its root path."""
    return init_project(tmp_path, InitOptions(name="e2e_proj"))


@pytest.fixture
def project_with_features(project: Path) -> Path:
    """Project with two feature files (login, checkout)."""
    add_feature(project, AddFeatureOptions(name="login", tags="smoke,auth"))
    add_feature(
        project, AddFeatureOptions(name="checkout", tags="smoke,regression", template="crud")
    )
    return project


@pytest.fixture
def project_with_steps(project_with_features: Path) -> Path:
    """Project with features plus HTTP and auth step libraries."""
    add_steps(project_with_features, AddStepsOptions(lib="http"))
    add_steps(project_with_features, AddStepsOptions(lib="auth"))
    return project_with_features


@pytest.fixture
def project_with_environment(project: Path) -> Path:
    """Project with environment.py rewritten with kit+data wiring."""
    add_environment(project, AddEnvironmentOptions(kit=True, data=True))
    return project


FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture
def openapi_yaml_spec(project: Path) -> Path:
    """Path to the Petstore OpenAPI 3.0 YAML fixture (copied into project)."""
    dest = project / "petstore.yaml"
    shutil.copy2(FIXTURES_DIR / "openapi" / "petstore.yaml", dest)
    return dest


@pytest.fixture
def openapi_json_spec(project: Path) -> Path:
    """Path to the Petstore OpenAPI 3.0 JSON fixture (copied into project)."""
    dest = project / "petstore.json"
    shutil.copy2(FIXTURES_DIR / "openapi" / "petstore.json", dest)
    return dest


@pytest.fixture
def swagger2_spec(project: Path) -> Path:
    """Path to the Swagger 2.0 JSON fixture (copied into project)."""
    dest = project / "petstore_swagger2.json"
    shutil.copy2(FIXTURES_DIR / "swagger" / "petstore_swagger2.json", dest)
    return dest


@pytest.fixture
def postman_collection(project: Path) -> Path:
    """Path to the Postman Collection v2.1 fixture (copied into project)."""
    dest = project / "sample_collection.json"
    shutil.copy2(FIXTURES_DIR / "postman" / "sample_collection.json", dest)
    return dest


@pytest.fixture
def cucumber_project(project: Path) -> Path:
    """Path to a copy of the Cucumber (Java) fixture project inside the project root."""
    dest = project / "cucumber_src"
    shutil.copytree(FIXTURES_DIR / "cucumber", dest)
    return dest


def run_behave_dry_run(cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run ``behave --dry-run`` in *cwd* and return the completed process."""
    return subprocess.run(
        [sys.executable, "-m", "behave", "--dry-run", "--no-color"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def run_ruff_check(cwd: Path, *targets: str) -> subprocess.CompletedProcess[str]:
    """Run ``ruff check`` on *targets* inside *cwd*."""
    return subprocess.run(
        [sys.executable, "-m", "ruff", "check", *targets],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def collect_files(root: Path) -> set[str]:
    """Return a set of relative file paths inside *root* (forward-slash normalised)."""
    return {
        str(p.relative_to(root)).replace("\\", "/")
        for p in root.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }


def parse_all_features(root: Path) -> list[Any]:
    """Parse every ``.feature`` file under *root* and return the parsed objects.

    Raises if any file fails to parse.
    """
    features: list[Any] = []
    for path in sorted(root.rglob("*.feature")):
        text = path.read_text(encoding="utf-8")
        features.append(_parse_feature(text, filename=safe_parse_feature_filename(path)))
    return features
