---
name: luxus-python-stack
description: Expert coding agent for the Luxurious Python Stack — a five-level Python development system using Mamba, UV, direnv, Ruff, MyPy, bump-my-version, and GitHub Actions. Use this skill whenever working on Python projects that use uv, mamba, or direnv; when initializing new Python projects with pyinit; when managing virtual environments (.venv) or conda environments; when running Ruff linting, MyPy type checking, or pytest; when bumping versions or releasing packages with bump-my-version; when setting up CI/CD pipelines for Python; when working with AGENTS.md or SESSION.md in a project repository; or when the user asks about the five-level Python stack concept (System, Data Science, Project, CI/Deployment, AI Agents).
---

# Luxurious Python Stack

## Overview

This skill provides expert knowledge of the Luxurious Python Stack — a five-level development workflow designed for flexible, conflict-free Python environment management. The stack separates concerns into distinct levels, each with specific tools and purposes.

To understand the full stack documentation, read `references/luxus-python-stack.md`. For a quick command lookup, see `references/daily-commands.md`.

## Five-Level Architecture

| Level | Name | Tool | Activation |
|-------|------|------|-----------|
| 0 | System/Global | `/usr/bin/python` | Always active (fallback) |
| 1 | Data Science | Mamba | `act <envname>` or startup via `.startenv` |
| 2 | Project/.venv | UV | Auto via `direnv` when `.venv` exists |
| 3 | CI/Deployment | GitHub Actions + UV | On push/PR or manual trigger |
| 4 | AI Agents | AGENTS.md + SESSION.md | Agent session start |

**Key principle**: Levels are isolated. Level 2 (.venv) overrides Level 1 (Mamba) in any directory with a `.venv` folder via `direnv`.

## Decision Tree: Which Tool to Use?

```
Starting fresh in a project directory?
  → Has .venv? → Already at Level 2 (direnv auto-activates)
  → No .venv?  → Run pyinit (see scripts/pyinit.sh) or uv init

Need to install a package?
  → In a project (.venv active): uv add <package>
  → In data science env:         uv pip install <package>  (fast)
  → System-wide:                 avoid (use virtual envs)

Need to run code?
  → In terminal with direnv:  python src/...  (env auto-active)
  → In scripts/CI:            uv run python src/...  (guaranteed sync)

Need to release?
  → uv run bump-my-version [patch|minor|major]
  → git push origin main --tags
```

## Core Workflows

### 1. Initialize a New Python Project

To create a new project, use the bundled [`scripts/pyinit.sh`](scripts/pyinit.sh) script:

```bash
# App project in current directory
bash scripts/pyinit.sh

# App project in a new directory
bash scripts/pyinit.sh my-project

# Library project
bash scripts/pyinit.sh my-lib --lib
```

The script creates:
- `src/<project>/` structure
- `pyproject.toml` with UV configuration
- `.venv/` virtual environment (Python 3.12)
- `.vscode/settings.json` with Ruff formatter
- `.envrc` for direnv auto-activation
- `.gitignore` (from gitignore.io)
- `bump-my-version` config in `pyproject.toml`
- Dev dependencies: `ruff pytest mypy colorlog bump-my-version`

After running pyinit, activate the environment:
```bash
direnv allow   # already done by pyinit, but run if .envrc exists
```

### 2. Environment Management

Naming convention:
The ds stands for data science, the 12 comes from Python 3.12

**Activate a Mamba environment (Level 1)**:
```bash
act ds12          # activates and saves to ~/.startenv
mamba activate ds12  # without saving
```

**Work with project environments (Level 2)**:
```bash
# direnv handles activation automatically when entering the directory
# If module errors arise after git pull:
uv sync
```

**Create/recreate a Mamba environment**:
```bash
py=3.12 && ENV_NAME="ds${py: -2}"
mamba deactivate
mamba remove -y -n $ENV_NAME --all 2>/dev/null
mamba create -y -n $ENV_NAME python=$py <packages...>
mamba activate $ENV_NAME
```

### 3. Daily Development Commands

**Add dependencies**:
```bash
uv add <package>          # runtime dependency
uv add --dev <package>    # dev-only dependency
uv sync                   # sync environment with lock file
```

**Run code**:
```bash
python src/my_project/main.py    # with direnv active
uv run python src/...            # guaranteed sync (use in scripts/CI)
pytest                           # run tests
```

**Code quality**:
```bash
ruff check .              # lint: find errors
ruff check --fix .        # lint: auto-fix
mypy src/                 # type checking
```

### 4. Release & Deployment

**ALWAYS use bump-my-version** — never edit versions or create tags manually:

```bash
# Patch release (bugfixes): 0.2.0 → 0.2.1
uv run bump-my-version patch

# Minor release (features): 0.2.1 → 0.3.0
uv run bump-my-version minor

# Major release (breaking): 0.3.0 → 1.0.0
uv run bump-my-version major

# Push code AND tags
git push origin main --tags
```

**Build and publish** (if not handled by CI):
```bash
uv build        # creates dist/
uv publish      # upload to PyPI
```

### 5. AI Agent Integration (Level 4)

Every repository using this stack includes two special files:

**`AGENTS.md`** (tracked in git):
- Contains project overview, architecture, and important decisions
- Tells the AI agent how to work on this project
- Includes file structure, conventions, and key commands
- Read this at the start of every agent session

**`SESSION.md`** (NOT tracked — in `.gitignore`):
- Volatile session memory: summary of the last agent session
- Recreate at the end of each session with: what was done, current state, next steps
- Read at session start to restore context

**Session start workflow**:
1. Read `AGENTS.md` for project context
2. Read `SESSION.md` if it exists (last session summary)
3. Run `uv sync` to ensure environment is current
4. Begin work

**Session end workflow**:
1. Write/update `SESSION.md` with session summary
2. Commit all changes
3. Run quality checks: `ruff check .` and `mypy src/`

## Key Shell Functions

These are bash functions defined in `.bashrc` — use them as commands:

| Function | Usage | Description |
|----------|-------|-------------|
| `pyinit` | `pyinit [name] [--lib]` | Create a new Python project |
| `act` | `act <envname>` | Activate Mamba env + save to `.startenv` |
| `cw` | `cw` / `cw .` | Jump to / set working folder |
| `pypurge` | `pypurge` | Clean pip cache + Mamba environment |

## Important Notes

1. **`uv run` vs direct execution**: In scripts and CI always use `uv run` (auto-syncs). In terminal with direnv active, direct `python` is fine.

2. **Never mix uv packages into Mamba**: In Level 1 (Mamba), `uv pip install` is used instead of `mamba install` for faster installs, but this means those packages aren't under Mamba's control. This is intentional — the data science environment is disposable and rebuilt regularly.

3. **Version bumping**: Never edit `version =` in `pyproject.toml` manually. Never `git tag` manually. Always use `bump-my-version`.

4. **direnv**: If auto-activation isn't working, run `direnv allow` in the project directory.

## References

- Full stack documentation: `references/luxus-python-stack.md`
- Quick command reference: `references/daily-commands.md`
