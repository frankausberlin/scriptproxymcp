set shell := ["bash", "-uc"]

# Luxurious Python Stack — Justfile for scriptproxymcp

# === Quality Gates ===

# Full quality gate: lint + typecheck + test (inlined to avoid subshell overhead)
check:
	uv run ruff check .
	uv run ruff format --check .
	uv run basedpyright
	uv run pytest tests/ -v --tb=short --cov=src --cov-report=term-missing

# Lint and format check (includes type checking)
lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run basedpyright

# Auto-fix lint and format issues
fix:
	uv run ruff check --fix .
	uv run ruff format .

# Type checking only
typecheck:
	uv run basedpyright

# Run tests
test:
	uv run pytest tests/ -v --cov=src --cov-report=term-missing

# === Security ===

# Run pip-audit for dependency vulnerability scanning (ephemeral, not a dev dep)
audit:
	uvx pip-audit

# === Release Workflow ===

# Bump version — requires a clean working tree (patch | minor | major)
bump part="patch":
	#!/usr/bin/env bash
	if ! git diff --quiet || ! git diff --cached --quiet; then
		echo "Error: Working tree is dirty. Commit or stash changes first." >&2
		exit 1
	fi
	uv run bump-my-version bump {{part}}

# === Developer Experience ===

# Run the project
run:
	uv run scriptproxymcp

# Quick dev test cycle
dev:
	uv run pytest tests/ -v --tb=short --cov=src --cov-report=term-missing

# Sync environment
sync:
	uv sync
