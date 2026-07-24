# Installation

## Requirements

- Python 3.11 or later.

## Install

```bash
pip install behave-gen
```

This installs `behave-gen` with its three base dependencies: `behave`,
`behave-model`, and `typer`.

## Optional extras

Each ecosystem tool is an optional extra. Install only what you need:

```bash
pip install behave-gen[doctor,lint,format,openapi]
```

Or install everything at once:

```bash
pip install behave-gen[all]
```

| Extra | Package | Used by |
| ----- | ------- | ------- |
| `doctor` | `behave-doctor` | `check`, `doctor` |
| `lint` | `behave-lint` | `lint` |
| `format` | `behave-format` | `format` |
| `openapi` | `pyyaml` | `from-openapi`, `from-swagger` |
| `jinja2` | `jinja2` | Custom templates with Jinja2 engine |
| `kit` | `behave-kit` | `add environment --kit` |
| `data` | `behave-data` | `add environment --data` |
| `all` | All of the above | — |

## Verify installation

```bash
behave-gen --help
```

```text
Usage: behave-gen [OPTIONS] COMMAND [ARGS]...

  Scaffold and evolve Behave BDD projects.
```

## Development install

```bash
git clone https://github.com/behave-gen/behave-gen.git
cd behave-gen
pip install -e ".[dev,docs]"
pre-commit install
```

See [Contributing](contributing.md) for full guidelines.
