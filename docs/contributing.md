# Contributing

Contributions are welcome! See [CONTRIBUTING.md](https://github.com/MathiasPaulenko/behave-gen/blob/main/CONTRIBUTING.md)
for full guidelines.

## Quick start

```bash
git clone https://github.com/MathiasPaulenko/behave-gen.git
cd behave-gen
pip install -e ".[dev,docs]"
pre-commit install
```

## Development commands

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
| `make docs-serve` | Serve documentation locally. |
| `make clean` | Remove build artifacts and caches. |

## Serving docs locally

```bash
pip install -e ".[docs]"
mkdocs serve
```

Documentation is available at `http://127.0.0.1:8000`.
