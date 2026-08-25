.PHONY: test lint typecheck imports check build docs

test:
	uv run pytest -v

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run mypy

imports:
	PYTHONPATH=src uv run lint-imports

check: lint typecheck imports test

build:
	uv build

docs:
	uv run mkdocs serve
