# Changelog

All notable changes to behave-gen are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.1] - 2026-07-27

### Fixed

- `_project_name` in `add environment` no longer crashes with `AttributeError`
  when `[project]` in `pyproject.toml` is a non-table value (e.g. a string).
- `_find_unquoted_close_bracket` now correctly handles TOML escape sequences:
  single-quoted (literal) strings treat backslash as a literal character, and
  double-quoted strings count consecutive backslashes to determine if the
  closing quote is escaped.
- `add environment` no longer deletes the existing `environment.py` before
  writing. The atomic write via `safe_write_text` preserves the original file
  if the write fails, preventing data loss.
- `update` no longer deletes generated step libraries or `environment.py`
  before re-applying templates. Atomic replacement via `tmp_path.replace(target)`
  preserves existing files on write failure.
- `_insert_into_inline_array` regex now correctly handles escaped quotes
  (`\"`) inside double-quoted TOML strings when parsing inline dependency
  arrays.
- Version fallback in `__init__.py` updated to match the version declared in
  `pyproject.toml`.
- `run` in `cli/app.py` now correctly reads `typer.Exit.exit_code` instead of
  the non-existent `code` attribute, and handles `None` exit codes.
- `_build_report_from_doctor` in `check.py` now uses `_safe_int` to parse
  `exit_code`, preventing crashes on non-numeric values.

### Changed

- `update` command imports `_BUILTIN_LIBRARIES` from `steps.py` instead of
  duplicating the dictionary (DRY).
- `_to_int_line` in `check.py` refactored to delegate to the new `_safe_int`
  helper.

## [1.1.0] - 2026-07-26

### Fixed

- Windows reserved-name validation for multi-dot names (e.g. `COM1.tar.gz`).
- `add_config` handling of inline and multiline `optional-dependencies` arrays with comments and quoted strings.
- OpenAPI/Swagger/Postman version parsing for numeric YAML/JSON values.
- Postman URL resolution for dictionary host/path segments and missing protocol.
- Empty or whitespace HTTP methods defaulting to `get` in Postman collections.
- Postman URL path variable rendering.
- Template discovery and rendering `OSError` handling.
- Feature filename sanitization for Windows reserved device names.
- Relative and absolute path resolution for generated output directories.
- Docstring coverage and style across the source package, including missing
  public-method, `__init__`, `__post_init__`, and argument descriptions.
- Escape-heavy docstrings in `add.py`, `environment.py`, and feature builders
  now use raw strings to satisfy D301.

### Changed

- `pyproject.toml` uses the PEP 621 `license` table and adds the `Typing :: Typed`,
  `Environment :: Console`, and `Operating System :: OS Independent` classifiers.
- Source distribution now includes `tests`, `examples`, `docs`, `Makefile`,
  `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and `SECURITY.md` alongside the
  source package.
- `dev` extras now include `bandit` and `pip-audit`.
- `Makefile` uses `python -m` consistently, builds into `ref/output/dist/`, and
  provides a cross-platform `clean` target.
- AGENTS.md, CONTRIBUTING.md, README.md, and docs now point to `ref/output/dist/`
  and use `python -m` / `pip_audit` consistently.
- CONTRIBUTING.md coverage threshold and PR template checklist aligned to 80%.
- `ruff` excludes generated `ref/output` artifacts and the `examples/` directory.
- `ruff` lint select now includes `D` (pydocstyle) for the source package with
  `D203` and `D213` ignored and `tests/**` excluded.
- Global `--dry-run` and `--verbose` options are hidden from `--help` because they
  are accepted for backward compatibility but not yet implemented.

## [1.0.0] - 2026-07-24

### Tests

- Unit, integration, and end-to-end tests covering all commands and workflows.
- E2E tests in `tests/e2e/` covering full workflows:
  `init` → `add feature` → `add steps` → `behave --dry-run`,
  `from-openapi` (YAML + JSON), `from-postman`, `from-swagger`,
  `migrate` (Cucumber), `check`/`stats`/`preview`, `add environment`/
  `add config`/`update`, and generated code quality (ruff, behave-model parse).

### Added

- `init` command: scaffolds a new Behave project from templates.
- `add feature` command: generates `.feature` files (default, CRUD templates).
- `add steps` command: adds real, runnable step libraries (HTTP, auth).
- `add environment` command: rewrites `environment.py` with kit/data wiring.
- `add config` command: adds ecosystem packages to `pyproject.toml`.
- `check` command: runs behave-doctor diagnostics with actionable suggestions.
- `doctor` command: alias for `check`.
- `lint` command: delegates to behave-lint CLI.
- `format` command: delegates to behave-format CLI.
- `from-openapi` command: generates features and HTTP steps from OpenAPI 3.x.
- `from-postman` command: generates features from Postman Collection v2.1.
- `from-swagger` command: converts Swagger 2.0 to OpenAPI 3.x and generates.
- `migrate` command: migrates Cucumber (Java) projects to Behave layout.
- `preview` command: pretty-prints `.feature` files.
- `stats` command: reports project statistics (features, scenarios, steps, tags).
- `update` command: upgrades generated files to latest behave-gen versions.
- Pluggable template engine with string and Jinja2 backends.
- Pluggable generator architecture (OpenAPI, Postman plugins).
- Optional dependency strategy via extras (doctor, lint, format, openapi, etc.).
- Example projects in `examples/` demonstrating init, from-openapi, and migrate.
- GitHub community files: issue templates, PR template, dependabot, contributing
  guide, code of conduct, security policy.
- Trusted Publishing (OIDC) release workflow to PyPI.
- ADR-0001: no empty step-definition skeletons.
- ADR-0002: modular monolith with plugin generators.
- ADR-0003: template engine design.
- ADR-0004: optional dependency strategy.
