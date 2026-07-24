"""Typer CLI application for behave-gen.

Phase 2 registers every command as a no-op placeholder that prints
``"not implemented yet"`` and exits with code ``1``. Real logic is wired in
later phases by delegating to ``behave_gen.commands.*`` modules.

The command set and global options match the conventions used by
``behave-doctor``.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from typing import Annotated

import typer

from behave_gen.commands.add import AddFeatureOptions, run_add_feature
from behave_gen.commands.check import run_check
from behave_gen.commands.environment import (
    AddEnvironmentOptions,
    run_add_config,
    run_add_environment,
)
from behave_gen.commands.format import run_format
from behave_gen.commands.from_openapi import FromOpenApiOptions, run_from_openapi
from behave_gen.commands.from_postman import FromPostmanOptions, run_from_postman
from behave_gen.commands.from_swagger import FromSwaggerOptions, run_from_swagger
from behave_gen.commands.init import InitOptions, run_init
from behave_gen.commands.lint import run_lint
from behave_gen.commands.migrate import MigrateOptions, run_migrate
from behave_gen.commands.preview import run_preview
from behave_gen.commands.stats import run_stats
from behave_gen.commands.steps import AddStepsOptions, run_add_steps
from behave_gen.commands.update import UpdateOptions, run_update

app = typer.Typer(
    name="behave-gen",
    help="Scaffold and evolve Behave BDD projects.",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
)

# Global option state, populated by the root callback and read by commands.
_PROJECT_OPTION: Annotated[str | None, typer.Option] = typer.Option(
    None, "--project", help="Project root directory (default: auto-detect)."
)
_CONFIG_OPTION: Annotated[str | None, typer.Option] = typer.Option(
    None, "--config", help="Path to an explicit pyproject.toml config file."
)
_VERBOSE_OPTION: Annotated[bool, typer.Option] = typer.Option(
    False, "--verbose", "-v", help="Enable verbose (DEBUG) output."
)
_DRY_RUN_OPTION: Annotated[bool, typer.Option] = typer.Option(
    False, "--dry-run", help="Show what would happen without writing files."
)


class _GlobalState:
    """Mutable container for global CLI options."""

    project: str | None = None
    config: str | None = None
    verbose: bool = False
    dry_run: bool = False


state = _GlobalState()


@app.callback()
def main_callback(
    project: Annotated[str | None, typer.Option] = _PROJECT_OPTION,
    config: Annotated[str | None, typer.Option] = _CONFIG_OPTION,
    verbose: Annotated[bool, typer.Option] = _VERBOSE_OPTION,
    dry_run: Annotated[bool, typer.Option] = _DRY_RUN_OPTION,
) -> None:
    """Configure global options shared by all subcommands."""
    state.project = project
    state.config = config
    state.verbose = verbose
    state.dry_run = dry_run


# --- Project lifecycle -----------------------------------------------------


@app.command("init")
def init_cmd(
    name: Annotated[str, typer.Argument(help="New project directory name.")],
    template: Annotated[str, typer.Option] = typer.Option(
        "default", "--template", help="Template set to use."
    ),
    kit: Annotated[bool, typer.Option] = typer.Option(
        False, "--kit", help="Pre-wire behave-kit in environment.py."
    ),
    data: Annotated[bool, typer.Option] = typer.Option(
        False, "--data", help="Pre-wire behave-data hooks."
    ),
    force: Annotated[bool, typer.Option] = typer.Option(
        False, "--force", help="Overwrite an existing directory."
    ),
) -> None:
    """Create a new Behave project from a template."""
    options = InitOptions(name=name, template=template, kit=kit, data=data, force=force)
    code = run_init(options)
    raise typer.Exit(code=code)


add_app = typer.Typer(help="Add features, steps, environment, or config to a project.")
app.add_typer(add_app, name="add")


@add_app.command("feature")
def add_feature_cmd(
    name: Annotated[str, typer.Argument(help="Feature name (without extension).")],
    tags: Annotated[str | None, typer.Option] = typer.Option(
        None, "--tags", help="Comma or space separated tags."
    ),
    template: Annotated[str, typer.Option] = typer.Option(
        "default", "--template", help="Feature template to use."
    ),
) -> None:
    """Add a .feature file to the project."""
    options = AddFeatureOptions(name=name, tags=tags, template=template)
    code = run_add_feature(options)
    raise typer.Exit(code=code)


@add_app.command("steps")
def add_steps_cmd(
    lib: Annotated[str, typer.Option] = typer.Option(
        ..., "--lib", help="Step library name (e.g. http, auth)."
    ),
    from_openapi: Annotated[str | None, typer.Option] = typer.Option(
        None, "--from-openapi", help="Generate steps from an OpenAPI spec."
    ),
) -> None:
    """Add real step definitions from a step library."""
    options = AddStepsOptions(lib=lib, from_openapi=from_openapi)
    code = run_add_steps(options)
    raise typer.Exit(code=code)


@add_app.command("environment")
def add_environment_cmd(
    kit: Annotated[bool, typer.Option] = typer.Option(
        False, "--kit", help="Add behave-kit fixtures."
    ),
    data: Annotated[bool, typer.Option] = typer.Option(
        False, "--data", help="Add behave-data hooks."
    ),
) -> None:
    """Add or update environment.py with ecosystem hooks."""
    options = AddEnvironmentOptions(kit=kit, data=data)
    code = run_add_environment(options)
    raise typer.Exit(code=code)


@add_app.command("config")
def add_config_cmd(
    name: Annotated[str, typer.Argument(help="Config to add (behave-kit, behave-data).")],
) -> None:
    """Add an ecosystem config to pyproject.toml."""
    code = run_add_config(name)
    raise typer.Exit(code=code)


# --- Codegen ---------------------------------------------------------------


@app.command("from-openapi")
def from_openapi_cmd(
    spec: Annotated[str, typer.Argument(help="Path to an OpenAPI 3.x spec.")],
    out_dir: Annotated[str, typer.Option] = typer.Option(
        "features", "--out-dir", help="Output directory for generated files."
    ),
    step_lib: Annotated[str | None, typer.Option] = typer.Option(
        None, "--step-lib", help="Step library to bind (e.g. http)."
    ),
    tag: Annotated[str | None, typer.Option] = typer.Option(
        None, "--tag", help="Tag generated scenarios."
    ),
    include_path: Annotated[list[str], typer.Option] = typer.Option(
        [], "--include-path", help="Restrict to these paths (repeatable)."
    ),
    include_method: Annotated[list[str], typer.Option] = typer.Option(
        [], "--include-method", help="Restrict to these HTTP methods (repeatable)."
    ),
) -> None:
    """Generate features and steps from an OpenAPI spec."""
    options = FromOpenApiOptions(
        spec=spec,
        out_dir=out_dir,
        step_lib=step_lib,
        tag=tag,
        include_paths=tuple(include_path),
        include_methods=tuple(include_method),
    )
    code = run_from_openapi(options)
    raise typer.Exit(code=code)


@app.command("from-postman")
def from_postman_cmd(
    collection: Annotated[str, typer.Argument(help="Path to a Postman collection JSON.")],
    out_dir: Annotated[str, typer.Option] = typer.Option(
        "features", "--out-dir", help="Output directory for generated files."
    ),
    step_lib: Annotated[str | None, typer.Option] = typer.Option(
        None, "--step-lib", help="Step library to bind (e.g. http)."
    ),
) -> None:
    """Generate features and steps from a Postman collection."""
    options = FromPostmanOptions(collection=collection, out_dir=out_dir, step_lib=step_lib)
    code = run_from_postman(options)
    raise typer.Exit(code=code)


@app.command("from-swagger")
def from_swagger_cmd(
    spec: Annotated[str, typer.Argument(help="Path to a Swagger 2.0 spec.")],
    out_dir: Annotated[str, typer.Option] = typer.Option(
        "features", "--out-dir", help="Output directory for generated files."
    ),
    step_lib: Annotated[str | None, typer.Option] = typer.Option(
        None, "--step-lib", help="Step library to bind (e.g. http)."
    ),
    tag: Annotated[str | None, typer.Option] = typer.Option(
        None, "--tag", help="Tag generated scenarios."
    ),
) -> None:
    """Generate features and steps from a Swagger 2.0 spec."""
    options = FromSwaggerOptions(spec=spec, out_dir=out_dir, step_lib=step_lib, tag=tag)
    code = run_from_swagger(options)
    raise typer.Exit(code=code)


@app.command("migrate")
def migrate_cmd(
    source_dir: Annotated[str, typer.Argument(help="Cucumber project to migrate.")],
    out_dir: Annotated[str, typer.Option] = typer.Option(
        ".", "--out-dir", help="Output directory for the Behave project."
    ),
    from_lang: Annotated[str, typer.Option] = typer.Option(
        "java", "--from", help="Source language (java, ruby)."
    ),
) -> None:
    """Migrate a Cucumber project to Behave."""
    options = MigrateOptions(source=source_dir, out_dir=out_dir)
    code = run_migrate(options)
    raise typer.Exit(code=code)


# --- Health and formatting -------------------------------------------------


@app.command("doctor")
def doctor_cmd() -> None:
    """Run behave-doctor diagnostics (alias for check)."""
    code = run_check()
    raise typer.Exit(code=code)


@app.command("lint")
def lint_cmd(
    fix: Annotated[bool, typer.Option] = typer.Option(
        False, "--fix", help="Apply fixes where possible."
    ),
) -> None:
    """Lint .feature files via behave-lint."""
    code = run_lint(fix=fix)
    raise typer.Exit(code=code)


@app.command("format")
def format_cmd(
    check: Annotated[bool, typer.Option] = typer.Option(
        False, "--check", help="Check formatting without writing."
    ),
) -> None:
    """Format .feature files via behave-format."""
    code = run_format(check=check)
    raise typer.Exit(code=code)


@app.command("check")
def check_cmd(
    fmt: Annotated[str, typer.Option] = typer.Option(
        "text", "--format", help="Output format: text or json."
    ),
) -> None:
    """Check project health via behave-doctor."""
    code = run_check(fmt=fmt)
    raise typer.Exit(code=code)


# --- Inspection -------------------------------------------------------------


@app.command("preview")
def preview_cmd(
    feature: Annotated[str, typer.Argument(help="Path to a .feature file.")],
    fmt: Annotated[str, typer.Option] = typer.Option(
        "text", "--format", help="Output format: text or json."
    ),
) -> None:
    """Preview a feature file with resolved examples and tables."""
    code = run_preview(feature)
    raise typer.Exit(code=code)


@app.command("stats")
def stats_cmd(
    fmt: Annotated[str, typer.Option] = typer.Option(
        "text", "--format", help="Output format: text or json."
    ),
    by_tag: Annotated[bool, typer.Option] = typer.Option(
        False, "--by-tag", help="Break down stats by tag."
    ),
) -> None:
    """Report project statistics."""
    _ = by_tag  # reserved for future per-tag breakdown
    code = run_stats(fmt=fmt)
    raise typer.Exit(code=code)


# --- Update -----------------------------------------------------------------


@app.command("update")
def update_cmd(
    from_openapi: Annotated[str | None, typer.Option] = typer.Option(
        None, "--from-openapi", help="Re-apply an OpenAPI generator."
    ),
    only_missing: Annotated[bool, typer.Option] = typer.Option(
        False, "--only-missing", help="Add only missing features/steps."
    ),
    force: Annotated[bool, typer.Option] = typer.Option(
        False, "--force", help="Regenerate and back up changed files."
    ),
) -> None:
    """Re-apply generators to an existing project."""
    options = UpdateOptions(force=force)
    code = run_update(options)
    raise typer.Exit(code=code)


def run(argv: Sequence[str] | None = None) -> int:
    """Programmatic entry point used by tests and ``python -m behave_gen``."""
    try:
        app(args=list(argv) if argv is not None else None, standalone_mode=False)
    except typer.Exit as exc:
        return int(getattr(exc, "code", 1))
    except SystemExit as exc:  # pragma: no cover - defensive.
        return int(exc.code) if isinstance(exc.code, int) else 1
    return 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
