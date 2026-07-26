# Agent Notes for behave-gen

## Validation commands

Run these before committing or finishing a task:

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy --strict behave_gen
python -m pytest
python -m pytest --cov=behave_gen --cov-report=term-missing
python -m bandit -r behave_gen
python -m pip_audit .
python -m build --outdir ref/output/dist
```

## Project conventions

- Python 3.11+.
- The public CLI is `behave-gen`; entry point is `behave_gen.cli.app:run`.
- `Project.from_root(root, config=None)` is the preferred way to load a project
  and resolve config-aware paths (`features_dir`, `steps_dir`,
  `environment_file`, `templates_dir`).
- Paths in config must stay inside the project root.
- Commands should use `Project` rather than hardcoding `features/`,
  `features/steps/`, or `environment.py`.
- Generators live in `behave_gen/generators/` and implement the `Generator`
  protocol.
- Step-library templates are in `behave_gen/step_libraries/` and use
  `$project_name` string substitution.

## Output artifacts

Any generated session artifacts (audit reports, logs, diagrams, and temporary
research output) are written to `ref/output/` (ignored by git) unless the user
explicitly requests a tracked file.
