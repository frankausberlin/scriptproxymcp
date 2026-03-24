#!/usr/bin/env bash
# pyinit.sh — Luxury Python Project Initializer
# Part of the Luxurious Python Stack
#
# Usage:
#   bash pyinit.sh                   # initialize current directory as app
#   bash pyinit.sh my-project        # create new directory and initialize as app
#   bash pyinit.sh my-lib --lib      # create new directory and initialize as library
#   bash pyinit.sh . --lib           # initialize current directory as library
#
# What it creates:
#   - uv project (app or library) with Python 3.12
#   - .venv/ virtual environment
#   - pyproject.toml with bump-my-version config
#   - .vscode/settings.json with Ruff formatter
#   - .envrc for direnv auto-activation
#   - .gitignore from gitignore.io (Python + Linux + VSCode)
#   - Dev dependencies: ruff pytest mypy colorlog bump-my-version
#   - Git repository (if not already initialized)

set -euo pipefail

# ─── Parse arguments ──────────────────────────────────────────────────────────
_dir="."
_type="--app"

for arg in "$@"; do
    case "$arg" in
        --lib)  _type="--lib" ;;
        *)      _dir="$arg" ;;
    esac
done

# ─── Step 1: Create and enter directory ───────────────────────────────────────
if [[ "$_dir" != "." ]]; then
    mkdir -p "$_dir"
    cd "$_dir"
fi

PROJECT_NAME="$(basename "$PWD")"
echo -e "\e[34m💎 Initializing $_type project in ${PROJECT_NAME}...\e[0m"

# ─── Step 2: UV init with managed Python ──────────────────────────────────────
# Force managed Python to avoid Mamba conflicts
export UV_PYTHON_PREFERENCE=only-managed
uv init "$_type" --python 3.12

# ─── Step 3: Add dev dependencies ─────────────────────────────────────────────
uv add --dev ruff pytest mypy colorlog bump-my-version

# ─── Step 4: VS Code configuration ────────────────────────────────────────────
mkdir -p .vscode
cat > .vscode/settings.json << 'VSCODE_EOF'
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.analysis.typeCheckingMode": "basic",
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
        "source.fixAll.ruff": "always",
        "source.organizeImports.ruff": "always"
    },
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "src",
        "tests"
    ],
    "python.terminal.activateEnvironment": true
}
VSCODE_EOF

# ─── Step 5: bump-my-version config ───────────────────────────────────────────
cat >> pyproject.toml << 'BUMP_EOF'

[tool.bumpversion]
current_version = "0.1.0"
commit = true
tag = true
commit_args = "-m 'chore: bump version from {current_version} to {new_version}'"

[[tool.bumpversion.files]]
filename = "pyproject.toml"
search = 'version = "{current_version}"'
replace = 'version = "{new_version}"'
BUMP_EOF

# ─── Step 6: direnv setup ─────────────────────────────────────────────────────
echo "source .venv/bin/activate" > .envrc
direnv allow

# ─── Step 7: Git + .gitignore ─────────────────────────────────────────────────
if [[ ! -d ".git" ]]; then
    git init
fi

# Fetch gitignore from gitignore.io
curl -s "https://www.toptal.com/developers/gitignore/api/python,linux,vscode" > .gitignore

# Append Luxurious Python Stack additions
cat >> .gitignore << 'GITIGNORE_EOF'

# Added by 'Luxurious Python Stack'
# volatile, agent-generated data
SESSION.md
# freestyle: here you can put whatever you want
ignore/
ign/
ignored/
ignored.txt
# end of 'Luxurious Python Stack'
GITIGNORE_EOF

# ─── Step 8: Final sync ───────────────────────────────────────────────────────
uv sync

echo ""
echo -e "\e[32m✨ Success! Project '${PROJECT_NAME}' is ready.\e[0m"
echo ""
echo "  Next steps:"
echo "  1. direnv allow   (if not yet activated)"
echo "  2. Start coding in src/${PROJECT_NAME//-/_}/"
echo "  3. Run tests with: pytest"
echo "  4. Lint with:      ruff check ."
echo "  5. Type check:     mypy src/"
echo ""
echo "  To release:"
echo "  uv run bump-my-version patch"
echo "  git push origin main --tags"
