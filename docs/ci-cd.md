# CI/CD Integration

## GitHub Actions

### Basic health check

Run `behave-gen check` on every push to verify project health:

```yaml
name: BDD Health

on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.13"
      - run: pip install behave-gen[doctor]
      - run: behave-gen check
```

### Full pipeline

Scaffold, check, lint, format, and run tests:

```yaml
name: BDD Pipeline

on: [push, pull_request]

jobs:
  bdd:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.13"
      - run: pip install behave-gen[all]
      - run: behave-gen check
      - run: behave-gen lint
      - run: behave-gen format --check
      - run: behave --dry-run
```

### Generate from OpenAPI in CI

Regenerate features from an OpenAPI spec on every push:

```yaml
- run: behave-gen from-openapi spec.yaml --out-dir gen --step-lib http --tag api
- run: behave-gen check
- run: behave
```

## Pre-commit hook

Use behave-gen as a pre-commit hook:

```yaml
repos:
  - repo: https://github.com/MathiasPaulenko/behave-gen
    rev: v1.2.0
    hooks:
      - id: behave-gen-check
```

The hook environment installs `behave-doctor` automatically
(`additional_dependencies`), so `check` runs real diagnostics.

## Exit codes

| Code | Meaning |
| ---- | ------- |
| `0` | Success / clean |
| `1` | Issues found, project error, or tool failure |
| `2` | CLI usage error (unknown option or missing argument) |
