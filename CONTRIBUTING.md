# Contributing to ScriptProxyMCP

Thank you for your interest in contributing!

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (package manager)
- [just](https://github.com/casey/just) (task runner)
- [direnv](https://direnv.net/) (optional, for auto-activation)

## Getting Started

```bash
git clone https://github.com/frankausberlin/scriptproxymcp.git
cd scriptproxymcp
uv sync
direnv allow          # optional — auto-activates .venv
uv run pre-commit install
```

## Development Workflow

1. Create a feature branch from `master`.
2. Make your changes in `src/scriptproxymcp/`.
3. Run the quality gate before committing:
   ```bash
   just check            # lint + typecheck + test
   just fix              # auto-fix lint/format issues
   ```
4. Commit — pre-commit hooks run automatically.
5. Open a Pull Request against `master`.

## Code Style

- **Formatting & Linting**: Ruff (configured in `pyproject.toml`).
- **Type Checking**: basedpyright in `standard` mode.
- **Docstrings**: Google-style.
- **Line length**: 120 characters.

## Release Process

Releases are handled by maintainers via `bump-my-version`. **Never** edit version numbers manually.

```bash
just bump patch       # bugfix: 0.3.0 → 0.3.1
just bump minor       # feature: 0.3.1 → 0.4.0
just bump major       # breaking: 0.4.0 → 1.0.0
git push origin master --tags
```

## Security Auditing

```bash
just audit            # runs pip-audit via uvx (ephemeral)
```
