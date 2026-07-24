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
	@echo "  make build         Build sdist + wheel into dist/"
	@echo "  make docs          Build documentation site"
	@echo "  make docs-serve    Serve documentation locally"
	@echo "  make clean         Remove build artifacts and caches"

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

lint:
	ruff check .

lint-fix:
	ruff check --fix .

format:
	ruff format .

format-check:
	ruff format --check .

test:
	pytest

test-cov:
	pytest --cov=behave_gen --cov-report=term-missing

build:
	python -m build

docs:
	mkdocs build --strict

docs-serve:
	mkdocs serve

clean:
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov site
