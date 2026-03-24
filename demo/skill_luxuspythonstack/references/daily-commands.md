# Daily Commands Reference — Luxurious Python Stack

Quick lookup for all common operations. For full documentation, see `luxus-python-stack.md`.

---

## Project Initialization

```bash
# App project in current directory
bash scripts/pyinit.sh

# App project in new directory
bash scripts/pyinit.sh <project-name>

# Library project
bash scripts/pyinit.sh <project-name> --lib

# Alternative: manual uv init
export UV_PYTHON_PREFERENCE=only-managed
uv init --app --python 3.12    # or --lib
uv add --dev ruff pytest mypy colorlog bump-my-version
echo "source .venv/bin/activate" > .envrc && direnv allow
```

---

## Environment Management

### Mamba (Level 1 — Data Science)
```bash
act <envname>                        # activate + save to ~/.startenv
mamba activate <envname>             # activate without saving
mamba deactivate                     # deactivate
mamba activate base                  # back to base

# Recreate environment
py=3.12 && ENV_NAME="ds${py: -2}"
mamba deactivate
mamba remove -y -n $ENV_NAME --all 2>/dev/null
mamba create -y -n $ENV_NAME python=$py <packages...>
mamba activate $ENV_NAME
```

### UV/direnv (Level 2 — Project)
```bash
# direnv auto-activates .venv when entering directory
direnv allow          # allow .envrc (run once per project)
uv sync               # sync environment after git pull / pyproject changes
```

---

## Dependencies

```bash
uv add <package>              # add runtime dependency
uv add --dev <package>        # add dev-only dependency
uv remove <package>           # remove dependency
uv sync                       # sync .venv with lock file
uv pip install <package>      # install directly (Level 1 / Level 3 only)
```

---

## Running Code

```bash
python src/<project>/main.py        # direct (with direnv active)
uv run python src/<project>/main.py # guaranteed sync (use in scripts/CI)
uv run <tool> <args>                # run tool from project environment
```

---

## Testing

```bash
pytest                      # run all tests
pytest tests/               # run specific directory
pytest -v                   # verbose output
pytest -k "test_name"       # run specific test
pytest --tb=short           # short traceback
uv run pytest               # guaranteed sync (CI/CD)
```

---

## Code Quality

```bash
ruff check .                # lint: show errors
ruff check --fix .          # lint: auto-fix what's possible
ruff format .               # format code

mypy src/                   # type checking
mypy --strict src/          # strict type checking

# All in one (recommended before commit):
ruff check --fix . && mypy src/ && pytest
```

---

## Version & Release

```bash
# ALWAYS use bump-my-version (never edit manually, never git tag manually)
uv run bump-my-version patch    # 0.2.0 → 0.2.1  (bugfixes)
uv run bump-my-version minor    # 0.2.1 → 0.3.0  (new features)
uv run bump-my-version major    # 0.3.0 → 1.0.0  (breaking changes)

# Push code AND tags together
git push origin main --tags

# Build and publish (if not via CI)
uv build        # creates dist/
uv publish      # upload to PyPI
```

---

## CI/CD (GitHub Actions)

```bash
# In GitHub Actions workflows:
uv sync                     # install all dependencies (uses uv.lock)
uv run ruff check .         # lint
uv run mypy src/            # type check
uv run pytest               # run tests
uv build && uv publish      # build and publish (release workflow)

# Trigger release via workflow_dispatch in GitHub:
# → bump-my-version runs automatically in CI
```

---

## Git Workflow

```bash
# Feature development
git checkout -b feature/my-feature
# ... make changes ...
ruff check --fix . && mypy src/ && pytest
git add -A && git commit -m "feat: description"
git push origin feature/my-feature

# Release
uv run bump-my-version patch
git push origin main --tags

# After git pull
uv sync     # always sync after pulling changes
```

---

## Bash Aliases & Functions

```bash
# ~/.bashrc functions (already defined if stack is set up):
pyinit [name] [--lib]    # create project (uses scripts/pyinit.sh)
act <envname>            # activate mamba env + save to ~/.startenv
cw                       # cd to saved working folder
cw .                     # save current folder as working folder
pypurge                  # clean pip cache + mamba environment
rlb                      # source ~/.bashrc (reload)
```

---

## AI Agent Session Workflow

### Session Start
```bash
# 1. Read project context
cat AGENTS.md

# 2. Read last session summary (if exists)
cat SESSION.md 2>/dev/null || echo "No previous session"

# 3. Sync environment
uv sync

# 4. Check project status
git status
git log --oneline -5
```

### Session End
```bash
# 1. Run quality checks
ruff check --fix . && mypy src/ && pytest

# 2. Commit all changes
git add -A && git commit -m "chore: end of session"

# 3. Update SESSION.md with summary
cat > SESSION.md << 'EOF'
# Session Summary — $(date +%Y-%m-%d)

## What was accomplished
- ...

## Current state
- ...

## Next steps
- ...
EOF

git add SESSION.md   # SESSION.md is in .gitignore, this won't commit it
```

---

## Navigation

```bash
cw .          # set current dir as working folder
cw            # cd to saved working folder
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Modules not found after `git pull` | `uv sync` |
| Wrong Python version in project | `uv python pin 3.12` |
| direnv not activating | `direnv allow` |
| Mamba env conflicts | `mamba clean --all` or recreate env |
| Type errors | Check `mypy src/` output |
| Lint errors | `ruff check --fix .` |
| bump-my-version fails | Ensure clean git state (`git status`) |
| Can't publish to PyPI | Check `uv publish --token <token>` |
