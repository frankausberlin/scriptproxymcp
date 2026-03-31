set shell := ["bash", "-uc"]

# Luxurious Python Stack - Justfile for scriptproxymcp

# === Quality Gates ===
check:
	just lint
	just typecheck
	just test

lint:
	uv run ruff check .
	uv run ruff format --check .

fix:
	uv run ruff check --fix .
	uv run ruff format .

typecheck:
	uv run basedpyright

test:
	uv run pytest tests/ -v --cov=src --cov-report=term-missing

# === Release Workflow ===
bump level="patch":
	uv run bump-my-version bump {{level}}

# === Developer Experience ===
run:
	uv run scriptproxymcp

dev:
	uv run pytest tests/ -v --tb=short --cov=src --cov-report=term-missing

sync:
	uv sync
