# Changelog

All notable changes to behave-gen are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
