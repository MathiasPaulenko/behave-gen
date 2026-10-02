# Changelog

All notable changes to behave-gen are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.3.0] - 2026-10-02

### Added

- `add feature --template NAME` now looks up `templates_dir/NAME.feature`
  before the built-in templates, so project-level custom feature templates
  actually work.
- `init --template` accepts a path to a directory containing a custom project
  template set.
- `init` honours the `template_engine` value from `[tool.behave-gen]` when
  `--template-engine` is not passed (via `--config` or the target directory's
  `pyproject.toml`).
- `.pre-commit-hooks.yaml` so the repo can be used as a pre-commit hook
  (`behave-gen-check`), as documented in `docs/ci-cd.md`.

### Fixed

- Generated `sample.feature` is now a runnable scenario with matching
  `features/steps/sample_steps.py`, so a fresh `init` project passes
  `behave`, `behave-gen lint` and `behave-gen format --check` out of the box
  (previously behave-lint reported BC002 for the scenario-less placeholder).
- `behave-gen migrate` no longer strips `# language: xx` directives: Behave
  supports them natively, and removing them made non-English features
  unparseable after migration.
- Generated projects now ship `behave.ini` instead of `behave.toml`: Behave
  1.3.x only reads `behave.ini`, `.behaverc`, `setup.cfg`, `tox.ini`, and
  `pyproject.toml`, so the generated `behave.toml` was silently ignored. The
  INI file uses `[behave]` keys (`paths`, `default_tags`) that Behave
  actually understands. `behave.toml` is still recognised as a project marker
  for existing projects.
- CLI usage errors (unknown options, missing arguments, misplaced global
  options) now print the error to stderr instead of exiting with code 2 and
  no output.
- `init --template-engine jinja2` no longer emits literal `$project_name`
  placeholders: the jinja2 engine also substitutes `$name` variables present
  in the context after the jinja2 pass. The engine option now defaults to the
  configured `template_engine` instead of always `string`.
- `update` no longer strips behave-kit/behave-data wiring from a generated
  `environment.py` when the `--kit`/`--data` flags are not repeated; existing
  imports are detected and preserved.
- `update` reports files whose content is already current as `Unchanged`
  instead of always claiming `Updated`.
- `recording.py`: the generated navigate step calls `context.page.goto()`
  (the real Playwright API) instead of the nonexistent `navigate()`, and the
  scroll step pattern is typed (`{y:d}`) with an `int` parameter.
- `check` suggestions now store the quoted step text in `step` instead of the
  full diagnostic message.
- `safe_parse_feature_filename` now recognises Windows-style absolute paths
  (drive-letter and UNC) even when running on POSIX hosts, fixing the
  `test_safe_parse_feature_filename_handles_windows_absolute` CI failures on
  Linux and macOS.
- `release.yml`: tag creation is now idempotent — the workflow no longer
  fails on re-runs when the release tag already exists.
- `add config` errors out on a malformed `optional-dependencies` array
  instead of inserting a stray line that produces invalid TOML.
- Tags emitted in generated features are now sorted and deduplicated, so
  generated files are stable under `behave-gen format --check`.
- Fixed broken links to `github.com/behave/behave-kit` and
  `behave/behave-data` in generated `environment.py` docstrings; they now
  point to PyPI.
- Regenerated the stale step libraries in `examples/` and converted their
  `behave.toml` to `behave.ini`.

### Changed

- Stale "phase" docstrings in `cli/app.py` and `commands/add.py` corrected.
- `--verbose` and `--dry-run` now print a notice that they are not
  implemented instead of being silently ignored.
- `docs/cli.md` clarifies that global options go before the subcommand;
  `docs/configuration.md`, `docs/templates.md`, `docs/step-libraries.md`,
  `docs/architecture.md`, `docs/ci-cd.md`, `docs/index.md`, and
  `docs/generators.md` were corrected to match actual behaviour.
- Docs now state that `from-postman` accepts Postman Collection v2.0 and
  v2.1, matching the parser.
- The `behave-gen-check` pre-commit hook now installs `behave-doctor` via
  `additional_dependencies`, so it runs real diagnostics instead of exiting
  as a no-op.

## [1.2.0] - 2026-08-11

### Added

- `add steps --from-recording`: generate concrete step definitions and a
  feature file from a wavexis recording YAML. Supported action types:
  `navigate`, `click` (by selector or text), `type`, and `scroll`. Steps
  are deduplicated against existing project definitions. Can be combined
  with `--lib` to add a library first, then dedup recording-derived steps.

### Fixed

- `plugins/openapi/parser.py`: `None` or missing `info.title` / `info.version` fields
  now fall back to defaults ("OpenAPI", "0.0.0") instead of producing the string
  `"None"`.
- `plugins/postman/parser.py`: `None` or missing `info.name`, `info.schema`, and
  item `name` fields now fall back to defaults instead of producing the string
  `"None"`.
- `recording.py`: scroll action `x` and `y` coordinates are now validated and
  coerced to integers at parse time via `_coerce_int`, rejecting `bool` and
  non-numeric types early instead of causing runtime errors in downstream
  Gherkin/step generation.
- `commands/migrate.py`: absolute source paths are now resolved and checked for
  project-root containment, matching the security pattern already used in
  `from-openapi` and `from-postman`. Previously, absolute paths bypassed the
  containment check entirely.
- `plugins/swagger/__init__.py`: YAML import error now points to the correct
  `swagger` extra instead of the `openapi` extra.
- `paths.py`: added `safe_parse_feature_filename` to avoid `ValueError` on
  Windows when `behave_model.parse_feature` receives a path on a different
  drive than the current working directory. Used in `add`, `preview`, and
  `stats` commands.

### Changed

- `docs/cli.md`: documented the `--from-recording` option for `add steps`.
- `docs/architecture.md`: added missing files (`recording.py`, `from_swagger.py`,
  `swagger.py` generator, `paths.py`) to the package structure listing.
- `docs/generators.md`: `from-swagger` now documents YAML support in addition to
  JSON.
- `docs/migration.md`: added note that source and output paths must be inside
  the project root.
- README: updated architecture listing to include `recording.py`, `paths.py`,
  `config.py`, and `project.py`.

## [1.1.3] - 2026-07-27

### Fixed

- Documentation: added clarifying note in `templates.md` that the `tags` variable
  includes a trailing newline, so `${tags}Feature:` renders as valid Gherkin.
- Documentation: `configuration.md` incorrectly stated `--config` was "not active".
- Documentation: `ci-cd.md` updated GitHub Actions versions (`@v7`) and pre-commit
  rev (`v1.1.3`).
- Documentation: `cli.md` was missing the `--path` option for `lint` and `format`.
- Documentation: `step-libraries.md` fixed `BASE_URL` → `DEFAULT_BASE_URL` and
  replaced misleading `<token>` placeholder.
- Documentation: `architecture.md` added missing `variants.py` to the file listing.
- Documentation: `installation.md` added missing `swagger` extra to the table.
- README: separated `swagger` extra, updated pinned action versions, added `docs`
  extra to dev install, added `make docs`/`make docs-serve` targets.

## [1.1.2] - 2026-07-27

### Fixed

- `http_steps.py.tpl`: merge duplicate `startswith` calls into a single tuple
  call to satisfy ruff `PIE810` on generated step libraries.
- `validate_name` in `paths.py`: absolute path detection now uses
  platform-appropriate check so `C:\project` on Windows and `/project` on Linux
  both raise the specific "absolute path" error instead of falling through to
  the forbidden-characters check.
- `test_diagnostics.py`: tests that require `behave-doctor` are now skipped
  when the extra is not installed, instead of failing on CI.
- `_build_config` in `config.py`: `isinstance` check for `[tool.behave-gen]`
  now runs before the falsy check, so non-dict values (e.g. `0`, `false`)
  raise `ValueError` instead of silently returning defaults.

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
