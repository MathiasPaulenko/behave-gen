# behave-gen

A CLI toolkit for scaffolding and evolving Behave BDD projects.

[![CI](https://github.com/MathiasPaulenko/behave-gen/actions/workflows/ci.yml/badge.svg)](https://github.com/MathiasPaulenko/behave-gen/actions/workflows/ci.yml)
[![Docs](https://github.com/MathiasPaulenko/behave-gen/actions/workflows/docs.yml/badge.svg)](https://mathiaspaulenko.github.io/behave-gen/)
[![PyPI](https://img.shields.io/pypi/v/behave-gen)](https://pypi.org/project/behave-gen/)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000)](https://docs.astral.sh/ruff/)
[![Types: mypy](https://img.shields.io/badge/types-mypy%20strict-blue)](https://mypy-lang.org/)

`behave-gen` helps you create, extend, and maintain Behave (Python BDD)
projects. It scaffolds new projects, generates `.feature` files and concrete
step definitions, integrates ecosystem tools (behave-doctor, behave-lint,
behave-format), and migrates Cucumber projects to Behave.

## Features

| Command | Description |
| ------- | ----------- |
| `init` | Scaffold a new Behave project with sensible defaults. |
| `add feature` | Generate `.feature` files from templates (default, CRUD). |
| `add steps` | Add real, runnable step libraries (HTTP, auth) or generate steps from a wavexis recording (`--from-recording`). No empty skeletons. |
| `add environment` | Rewrite `environment.py` with behave-kit/behave-data wiring. |
| `add config` | Add ecosystem packages to `pyproject.toml` idempotently. |
| `check` | Run behave-doctor diagnostics with actionable suggestions. |
| `doctor` | Alias for `check`. |
| `lint` | Lint `.feature` files via behave-lint. |
| `format` | Format `.feature` files via behave-format. |
| `from-openapi` | Generate features and HTTP steps from an OpenAPI 3.x spec. |
| `from-postman` | Generate features from a Postman Collection v2.1. |
| `from-swagger` | Convert Swagger 2.0 to OpenAPI 3.x and generate features. |
| `migrate` | Migrate a Cucumber (Java) project to Behave. |
| `preview` | Pretty-print a `.feature` file. |
| `stats` | Report project statistics (features, scenarios, steps, tags). |
| `update` | Re-apply generated environment and step libraries. |

## Installation

```bash
pip install behave-gen
```

### Requirements

- Python 3.11 or newer.
- A working `pip` / `venv` environment.

Optional extras extend functionality as shown below.

With optional extras:

```bash
pip install behave-gen[doctor,lint,format,openapi]
pip install behave-gen[all]
```

| Extra | Provides |
| ----- | -------- |
| `doctor` | `behave-doctor` — static analysis for `check`/`doctor`. |
| `lint` | `behave-lint` — Gherkin linting for `lint`. |
| `format` | `behave-format` — Gherkin formatting for `format`. |
| `openapi` | `pyyaml` — YAML parsing for `from-openapi`. |
| `swagger` | `pyyaml` — YAML parsing for `from-swagger`. |
| `jinja2` | `jinja2` — alternative template engine. |
| `kit` | `behave-kit` — environment hooks. |
| `data` | `behave-data` — test data fixtures. |
| `all` | All of the above. |

## Quick start

```bash
# Create a new Behave project
behave-gen init my-project
cd my-project

# Add a feature file
behave-gen add feature login

# Add HTTP step definitions
behave-gen add steps --lib http

# Generate steps from a wavexis recording
behave-gen add steps --from-recording recording.yaml

# Combine a step library with a recording (library first, then dedup)
behave-gen add steps --lib http --from-recording recording.yaml

# Check project health
behave-gen check

# Run tests
behave
```

## Generating from an OpenAPI spec

```bash
behave-gen from-openapi spec.yaml --out-dir gen --step-lib http --tag api
```

This produces `.feature` files grouped by path, each with scenarios that use
the HTTP step library syntax. The `--step-lib http` flag also generates a
concrete, runnable `http_steps.py` module.

## Generating steps from a wavexis recording

Use [`wavexis`](https://github.com/lvckaa/wavexis) to record browser
interactions, then generate Behave step definitions and a feature file from
the recording:

```bash
# Record a flow with wavexis (produces recording.yaml)
# Then generate steps and a feature file:
behave-gen add steps --from-recording recording.yaml
```

This produces:

- `features/steps/recorded_steps.py` — Python step definitions with real
  browser actions via `context.page` (Playwright/wavexis page object).
- `features/recorded.feature` — a Gherkin feature file representing the
  recorded flow.

Supported action types: `navigate`, `click` (by selector or text), `type`,
and `scroll`. Unsupported actions are silently skipped. Steps are
deduplicated against existing step definitions in the project.

You can combine `--from-recording` with `--lib` to add a step library first,
then generate recording-derived steps deduplicated against it.

## Migrating from Cucumber

```bash
behave-gen migrate path/to/cucumber-project --out-dir migrated
```

Feature files are copied into a Behave `features/` layout. Java step
definitions are not auto-translated; use `behave-gen add steps` to generate
Python equivalents.

## Examples

The [`examples/`](examples/) directory contains ready-to-run projects that
demonstrate each workflow:

- **[`basic-project`](examples/basic-project/)** — `init` + `add feature` +
  `add steps` with HTTP and auth step libraries.
- **[`openapi-project`](examples/openapi-project/)** — `from-openapi` generating
  features and HTTP steps from a Petstore OpenAPI 3.0 spec.
- **[`migrated-project`](examples/migrated-project/)** — `migrate` converting a
  Cucumber (Java) project to Behave feature files.

See [`examples/README.md`](examples/README.md) for details.

## Architecture

```text
behave_gen/
  cli/            Typer CLI application
  commands/       One module per CLI command
  generators/     Pluggable code generators (OpenAPI, Postman, Swagger)
  plugins/        Source-specific parsers and builders
  step_libraries/ Built-in step library templates (HTTP, auth)
  templates/      Project and feature templates
  config.py       [tool.behave-gen] configuration model
  diagnostics.py  Optional-dependency handling
  paths.py        Path resolution and validation helpers
  project.py      Project detection and state
  recording.py    Wavexis recording parser and step generator
```

## Supply chain & trust

- **Trusted Publishing (OIDC)** — releases to PyPI use
  [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) via GitHub
  Actions OIDC. No long-lived API tokens are stored in secrets.
- **Pinned actions** — all GitHub Actions are pinned to specific versions
  (e.g. `@v7`, `@v1.14.1`).
- **Minimal dependencies** — only `behave`, `behave-model`, and `typer` at
  runtime. All other dependencies are optional extras.
- **`py.typed` marker** — the package ships with inline type hints.
- **Reproducible builds** — `hatchling` build backend with no dynamic metadata.

## Development

```bash
git clone https://github.com/MathiasPaulenko/behave-gen.git
cd behave-gen
pip install -e ".[dev,docs]"
pre-commit install
```

| Command | Description |
| ------- | ----------- |
| `make help` | Show all available targets. |
| `make dev` | Install with dev extras. |
| `make lint` | Run `ruff check` + `mypy --strict`. |
| `make lint-fix` | Auto-fix lint issues. |
| `make format` | Format the code with `ruff format`. |
| `make format-check` | Verify formatting without changes. |
| `make test` | Run the test suite. |
| `make test-cov` | Run tests with coverage. |
| `make build` | Build sdist + wheel into `ref/output/dist/`. |
| `make docs` | Build documentation site. |
| `make docs-serve` | Serve documentation locally. |
| `make clean` | Remove build artifacts and caches. |

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

## Documentation

Full documentation, including the CLI reference, configuration guide, and
Python API docs, is published at
[mathiaspaulenko.github.io/behave-gen](https://mathiaspaulenko.github.io/behave-gen/).

## Acknowledgements

- Built on top of [Behave](https://behave.readthedocs.io/) and the Python
  packaging ecosystem.
- Template and scaffolding patterns inspired by the Python open source
  community's emphasis on minimal, composable tools.

## License

[MIT](LICENSE)
