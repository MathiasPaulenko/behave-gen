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

from behave_gen.config import BehaveGenConfig, load_config_at

app = typer.Typer(
    name="behave-gen",
    help="Scaffold and evolve Behave BDD projects.",
    no_args_is_help=False,
    invoke_without_command=True,
    add_completion=False,
    rich_markup_mode="rich",
)

# Global option state, populated by the root callback and read by commands.
_PROJECT_OPTION: Annotated[str | None, typer.Option] = typer.Option(
    None, "--project", help="Project root directory (default: current working directory)."
)
_CONFIG_OPTION: Annotated[str | None, typer.Option] = typer.Option(
    None, "--config", help="Path to an explicit pyproject.toml config file."
)
_VERBOSE_OPTION: Annotated[bool, typer.Option] = typer.Option(
    False, "--verbose", "-v", help="Enable verbose (DEBUG) output.", hidden=True
)
_DRY_RUN_OPTION: Annotated[bool, typer.Option] = typer.Option(
    False, "--dry-run", help="Show what would happen without writing files.", hidden=True
)


class _GlobalState:
    """Mutable container for global CLI options."""

    project: str | None = None
    config: str | None = None
    config_obj: BehaveGenConfig | None = None


state = _GlobalState()


def _load_state_config(config_path: str | None) -> BehaveGenConfig | None:
    """Load an explicit config file for use by subcommands."""
    if config_path is None:
        return None
    try:
        return load_config_at(config_path)
    except (OSError, ValueError) as exc:
        print(f"behave-gen: Invalid config: {exc}", file=sys.stderr)
        raise typer.Exit(code=1) from exc


@app.callback()
def main_callback(
    ctx: typer.Context,
    project: Annotated[str | None, typer.Option] = _PROJECT_OPTION,
    config: Annotated[str | None, typer.Option] = _CONFIG_OPTION,
    verbose: Annotated[bool, typer.Option] = _VERBOSE_OPTION,
    dry_run: Annotated[bool, typer.Option] = _DRY_RUN_OPTION,
) -> None:
    """Configure global options shared by all subcommands.

    When no subcommand is given, prints help and exits cleanly with code 0.
    """
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(0)

    state.project = project
    state.config = config
    state.config_obj = _load_state_config(config)


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
    template_engine: Annotated[str, typer.Option] = typer.Option(
        "string", "--template-engine", help="Template engine: string or jinja2."
    ),
) -> None:
    """Create a new Behave project from a template."""
    from behave_gen.commands.init import InitOptions, run_init

    options = InitOptions(
        name=name,
        template=template,
        kit=kit,
        data=data,
        force=force,
        template_engine=template_engine,
    )
    code = run_init(options, target_dir=state.project)
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
    from behave_gen.commands.add import AddFeatureOptions, run_add_feature

    options = AddFeatureOptions(name=name, tags=tags, template=template)
    code = run_add_feature(options, project_root=state.project, config=state.config_obj)
    raise typer.Exit(code=code)


@add_app.command("steps")
def add_steps_cmd(
    lib: Annotated[str, typer.Option] = typer.Option(
        ..., "--lib", help="Step library name (e.g. http, auth)."
    ),
) -> None:
    """Add real step definitions from a step library."""
    from behave_gen.commands.steps import AddStepsOptions, run_add_steps

    options = AddStepsOptions(lib=lib)
    code = run_add_steps(options, project_root=state.project, config=state.config_obj)
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
    from behave_gen.commands.environment import AddEnvironmentOptions, run_add_environment

    options = AddEnvironmentOptions(kit=kit, data=data)
    code = run_add_environment(options, project_root=state.project, config=state.config_obj)
    raise typer.Exit(code=code)


@add_app.command("config")
def add_config_cmd(
    name: Annotated[str, typer.Argument(help="Config to add (behave-kit, behave-data).")],
) -> None:
    """Add an ecosystem config to pyproject.toml."""
    from behave_gen.commands.environment import run_add_config

    code = run_add_config(name, project_root=state.project, config=state.config_obj)
    raise typer.Exit(code=code)


# --- Codegen ---------------------------------------------------------------


@app.command("from-openapi")
def from_openapi_cmd(
    spec: Annotated[str, typer.Argument(help="Path to an OpenAPI 3.x spec.")],
    out_dir: Annotated[str, typer.Option] = typer.Option(
        "gen",
        "--out-dir",
        help="Output directory for the generated project (a features/ subdir is created).",
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
    from behave_gen.commands.from_openapi import FromOpenApiOptions, run_from_openapi

    options = FromOpenApiOptions(
        spec=spec,
        out_dir=out_dir,
        step_lib=step_lib,
        tag=tag,
        include_paths=tuple(include_path),
        include_methods=tuple(include_method),
    )
    code = run_from_openapi(options, project_root=state.project, config=state.config_obj)
    raise typer.Exit(code=code)


@app.command("from-postman")
def from_postman_cmd(
    collection: Annotated[str, typer.Argument(help="Path to a Postman collection JSON.")],
    out_dir: Annotated[str, typer.Option] = typer.Option(
        "gen",
        "--out-dir",
        help="Output directory for the generated project (a features/ subdir is created).",
    ),
    step_lib: Annotated[str | None, typer.Option] = typer.Option(
        None, "--step-lib", help="Step library to bind (e.g. http)."
    ),
    tag: Annotated[str | None, typer.Option] = typer.Option(
        None, "--tag", help="Tag generated scenarios."
    ),
) -> None:
    """Generate features and steps from a Postman collection."""
    from behave_gen.commands.from_postman import FromPostmanOptions, run_from_postman

    options = FromPostmanOptions(collection=collection, out_dir=out_dir, step_lib=step_lib, tag=tag)
    code = run_from_postman(options, project_root=state.project, config=state.config_obj)
    raise typer.Exit(code=code)


@app.command("from-swagger")
def from_swagger_cmd(
    spec: Annotated[str, typer.Argument(help="Path to a Swagger 2.0 spec.")],
    out_dir: Annotated[str, typer.Option] = typer.Option(
        "gen",
        "--out-dir",
        help="Output directory for the generated project (a features/ subdir is created).",
    ),
    step_lib: Annotated[str | None, typer.Option] = typer.Option(
        None, "--step-lib", help="Step library to bind (e.g. http)."
    ),
    tag: Annotated[str | None, typer.Option] = typer.Option(
        None, "--tag", help="Tag generated scenarios."
    ),
) -> None:
    """Generate features and steps from a Swagger 2.0 spec."""
    from behave_gen.commands.from_swagger import FromSwaggerOptions, run_from_swagger

    options = FromSwaggerOptions(spec=spec, out_dir=out_dir, step_lib=step_lib, tag=tag)
    code = run_from_swagger(options, project_root=state.project, config=state.config_obj)
    raise typer.Exit(code=code)


@app.command("migrate")
def migrate_cmd(
    source_dir: Annotated[str, typer.Argument(help="Cucumber project to migrate.")],
    out_dir: Annotated[str, typer.Option] = typer.Option(
        "migrated",
        "--out-dir",
        help="Output directory for the migrated project (a features/ subdir is created).",
    ),
) -> None:
    """Migrate a Cucumber project to Behave."""
    from behave_gen.commands.migrate import MigrateOptions, run_migrate

    options = MigrateOptions(source=source_dir, out_dir=out_dir)
    code = run_migrate(options, project_root=state.project, config=state.config_obj)
    raise typer.Exit(code=code)


# --- Health and formatting -------------------------------------------------


@app.command("doctor")
def doctor_cmd() -> None:
    """Run behave-doctor diagnostics (alias for check)."""
    from behave_gen.commands.check import run_check

    code = run_check(project_root=state.project, config=state.config_obj)
    raise typer.Exit(code=code)


@app.command("lint")
def lint_cmd(
    fix: Annotated[bool, typer.Option] = typer.Option(
        False, "--fix", help="Apply fixes where possible."
    ),
    paths: Annotated[list[str], typer.Option] = typer.Option(
        [], "--path", help="Path to lint (repeatable); defaults to the features directory."
    ),
) -> None:
    """Lint .feature files via behave-lint."""
    from behave_gen.commands.lint import run_lint

    code = run_lint(
        project_root=state.project, fix=fix, paths=paths or None, config=state.config_obj
    )
    raise typer.Exit(code=code)


@app.command("format")
def format_cmd(
    check: Annotated[bool, typer.Option] = typer.Option(
        False, "--check", help="Check formatting without writing."
    ),
    paths: Annotated[list[str], typer.Option] = typer.Option(
        [], "--path", help="Path to format (repeatable); defaults to the features directory."
    ),
) -> None:
    """Format .feature files via behave-format."""
    from behave_gen.commands.format import run_format

    code = run_format(
        project_root=state.project, check=check, paths=paths or None, config=state.config_obj
    )
    raise typer.Exit(code=code)


@app.command("check")
def check_cmd(
    fmt: Annotated[str, typer.Option] = typer.Option(
        "text", "--format", help="Output format: text or json."
    ),
) -> None:
    """Check project health via behave-doctor."""
    from behave_gen.commands.check import run_check

    code = run_check(project_root=state.project, fmt=fmt, config=state.config_obj)
    raise typer.Exit(code=code)


# --- Inspection -------------------------------------------------------------


@app.command("preview")
def preview_cmd(
    feature: Annotated[str, typer.Argument(help="Path to a .feature file.")],
) -> None:
    """Preview a feature file with resolved examples and tables."""
    from behave_gen.commands.preview import run_preview

    code = run_preview(feature, project_root=state.project, config=state.config_obj)
    raise typer.Exit(code=code)


@app.command("stats")
def stats_cmd(
    fmt: Annotated[str, typer.Option] = typer.Option(
        "text", "--format", help="Output format: text or json."
    ),
) -> None:
    """Report project statistics."""
    from behave_gen.commands.stats import run_stats

    code = run_stats(project_root=state.project, fmt=fmt, config=state.config_obj)
    raise typer.Exit(code=code)


# --- Update -----------------------------------------------------------------


@app.command("update")
def update_cmd(
    kit: Annotated[bool, typer.Option] = typer.Option(
        False, "--kit", help="Include behave-kit wiring in environment.py."
    ),
    data: Annotated[bool, typer.Option] = typer.Option(
        False, "--data", help="Include behave-data wiring in environment.py."
    ),
    force: Annotated[bool, typer.Option] = typer.Option(
        False, "--force", help="Regenerate generated files even if they have been modified."
    ),
) -> None:
    """Re-apply generated environment and step libraries to an existing project."""
    from behave_gen.commands.update import UpdateOptions, run_update

    options = UpdateOptions(kit=kit, data=data, force=force)
    code = run_update(options, project_root=state.project, config=state.config_obj)
    raise typer.Exit(code=code)


def run(argv: Sequence[str] | None = None) -> int:
    """Programmatic entry point used by tests and ``python -m behave_gen``."""
    try:
        result = app(args=list(argv) if argv is not None else None, standalone_mode=False)
    except typer.Exit as exc:
        code = getattr(exc, "exit_code", 1)
        return 1 if code is None else int(code)
    except SystemExit as exc:  # pragma: no cover - defensive.
        return int(exc.code) if isinstance(exc.code, int) else 1
    except (OSError, RuntimeError) as exc:
        print(f"behave-gen: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        # Click/Typer usage errors (e.g. unknown options) carry an exit_code.
        exit_code = getattr(exc, "exit_code", None)
        if isinstance(exit_code, int):
            return exit_code
        raise
    if isinstance(result, int):
        return result
    return 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
