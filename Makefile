.PHONY: help install dev lint lint-fix format format-check test test-cov build docs docs-serve clean

help:
	@echo "Available targets:"
	@echo "  make dev           Install with dev extras"
	@echo "  make lint          Run ruff check + mypy --strict"
	@echo "  make lint-fix      Auto-fix lint issues"
	@echo "  make format        Format the code with ruff format"
	@echo "  make format-check  Verify formatting without changes"
	@echo "  make test          Run the test suite"
	@echo "  make test-cov      Run tests with coverage"
	@echo "  make build         Build sdist + wheel into ref/output/dist/"
	@echo "  make docs          Build documentation site"
	@echo "  make docs-serve    Serve documentation locally"
	@echo "  make clean         Remove build artifacts and caches"

install:
	python -m pip install -e .

dev:
	python -m pip install -e ".[dev]"

lint:
	python -m ruff check .
	python -m mypy --strict behave_gen

lint-fix:
	python -m ruff check --fix .

format:
	python -m ruff format .

format-check:
	python -m ruff format --check .

test:
	python -m pytest

test-cov:
	python -m pytest --cov=behave_gen --cov-report=term-missing

build:
	python -m build --outdir ref/output/dist

docs:
	python -m mkdocs build --strict

docs-serve:
	python -m mkdocs serve

clean:
	python -c "import glob, os, pathlib, shutil; \
	[shutil.rmtree(p, ignore_errors=True) for p in ['build', 'dist', '.pytest_cache', '.mypy_cache', '.ruff_cache', 'htmlcov', 'site']] + \
	[shutil.rmtree(p, ignore_errors=True) for p in glob.glob('*.egg-info')] + \
	[shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')] + \
	[[os.remove(p) for p in ['.coverage'] if os.path.exists(p)]]"
