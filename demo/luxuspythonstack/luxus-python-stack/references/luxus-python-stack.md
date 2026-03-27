## 💎 Luxurious Python Stack

<table width=1200><tr></tr><tr><td colspan=5><hr></td></tr><tr><td align=center>

🧱 Level 0<br><br>Global / System
</td><td align=center>

🧱 Level 1<br><br>Data Science / Jupyter
</td><td align=center>

🧱 Level 2<br><br>Projects / .venv
</td><td align=center>

🧱 Level 3<br><br>CI / Deployment
</td><td align=center>

🧱 Level 4<br><br>AI Agents / Vibe Coding
</td></tr><tr><td colspan=5><hr></td></tr></table>

Ultimately, it is a combination of tools, scripts and aliases that allow me to work efficiently and flexibly with Python. By separating it into different levels, I can ensure that I always have the right environment for my projects without causing conflicts between different projects or Python environments.

Tools:
- **Mamba**: A fast and efficient package manager that allows me to create and manage Python environments easily.
- **UV**: A tool for managing Python versions and virtual environments, which I use to switch between different Python versions and environments seamlessly.
- **direnv**: A tool that allows me to automatically load and unload environment variables based on the directory I am in, which is particularly useful for managing project-specific environments and dependencies.
- **Ruff & MyPy**: Tools for linting and type checking.
- **bump-my-version**: Automated publishing.

Scripts and Aliases:
- **cw**: `cw` -> change to working folder / `cw .` -> make current folder the working folder.
- **act**: Activates a Mamba environment and saves it in the file ~/.startenv.
- **pyinit**: Creates a Python project with all files and folders (src, tests, pyproject.toml, etc.) and initializes a UV environment.
- **pypurge**: An alias for purging the pip cache and cleaning the Mamba environment.


### Five-level concept

My workflow is based on a five-level concept:

0. **Global / System Level**

* The standard Python is available here (/usr/bin/python).
* Important tools such as git, rg, fd and the build essentials are installed.
* UV, direnv and Mamba are also installed but not set up.
* The system level is automatically active as soon as no other environment is activated.

1. **Data Science Level**

* This level is for data science work and is set up using Mamba.
* It includes tools like Jupyter Lab, pytorch, tensorflow, scikit-learn, and other data science libraries.
* This level is always active if there is no .venv folder in the current location or you deactivate it.
* Using `act` to activate an environment will automatically activate it in new terminals (.startenv).

2. **Project / .venv Level**

* This level is intended for folders with .venv, for example for projects.
* As soon as there is a .venv folder in the current folder, it will be automatically activated (after direnv activate).
* With `pyinit` you can quickly create a new project with a .venv folder and have the required files and folders created.
* If you prefer to work with uv venv / init yourself, this is not a problem, as direnv automatically activates .venv if you want.

3. **CI / Deployment Level**

* This level acts as the automated gatekeeper between local development and production/publishing. It is primarily powered by GitHub Actions.
* Environment Parity: Thanks to uv.lock, the CI server exactly mirrors the Level 2 project environment. The CI pipeline runs uv sync to ensure 100% reproducible builds.
* Continuous Integration (CI): On every push or Pull Request, automated workflows run the identical code quality checks used locally: uv run ruff check, uv run mypy, and uv run pytest. Code that fails here cannot be merged.
* Release Automation: Versioning and Git tagging are fully automated to prevent human error. Using a manual trigger (workflow_dispatch) in GitHub Actions, bump-my-version handles the version bump, commit, and tagging in a single atomic step.
* Automated building and publishing to PyPI via uv build and uv publish.


4. **AI Agents / Vibe Coding Level**

* **AGENTS.md** is part of the repository. Here you will find relevant information for an AI agent to understand and work on the project.
* **SESSION.md** is not part of the repository and is in .gitignore. It is a volatile file that contains the summary of the last session and is recreated by the agent for each session.
* **LuxusPythonStack Skill** is a Kilo Code skill (`luxus-python-stack`) that turns any AI coding agent into an expert on this stack. It provides:
  - Full knowledge of the five-level architecture and which tool to use when
  - A bundled `pyinit.sh` script for deterministic project initialization
  - Session workflow: reading `AGENTS.md` on start, writing `SESSION.md` on end
  - Quick command reference for all daily operations

⚠️ **Important Note Regarding the "Data Science Level":**<br>
> <b><font color=blue>It doesn't necessarily have to be data science. Any domain is possible here;</font></b> it just happens to be mine.<br>
> It's generally not recommended to use `uv` in a Mamba environment, as the packages installed this way are not under Mamba's control. This can lead to conflicts when updating packages with Mamba.<br>
> I use the data science environment in a way that makes this problem irrelevant. I'm constantly installing new libraries, deleting old ones, and experimenting. But just as frequently (sometimes twice a day), I completely wipe the environment (reinstall it).

```shell
mamba deactivate
mamba remove -y -n <envname> --all
mamba create -y -n <envname> ...
```
> That's why I use `uv`; it's so incredibly fast.

### Installation

```shell
sudo apt update && sudo apt install python3 direnv
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash Miniforge3-$(uname)-$(uname -m).sh
curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install ruff@latest

# use main trunk
git config --global init.defaultBranch main
```


### Scripts

```shell
cw () { [[ "$1" == "." ]] && echo "$PWD" > "$HOME/.config/current_working_folder" || cd "$(cat "$HOME/.config/current_working_folder")"; }
```

```shell
alias rlb="source ~/.bashrc"
```

```shell
act() { [ "$#" -ne 0 ] && echo $1 > ~/.startenv && mamba activate $1; }
```

```shell
# pyinit: Luxury Python Project Initializer (Usage: pyinit [project_name] [--lib])
pyinit() {
    # 0. Parse arguments: check for --lib flag and extract directory name
    local _dir="."; local _type="--app"; for arg in "$@"; do [[ "$arg" == "--lib" ]] && _type="--lib" || _dir="$arg"; done
    # 1. Create and enter directory (if a name was passed)
    [[ "$_dir" != "." ]] && mkdir -p "$_dir" && cd "$_dir"
    echo -e "\e[34m💎 Initializing $_type project in $(basename "$PWD")...\e[0m"
    # forcing managed Python to avoid mamba conflicts and uv init it.
    export UV_PYTHON_PREFERENCE=only-managed && uv init $_type --python 3.12
    # 2. Add essential Dev-Tools (inkl. bump-my-version)
    uv add --dev ruff pytest mypy colorlog bump-my-version
    # 3. Setup VS Code Configuration (compact JSON)
    mkdir -p .vscode && cat <<EOF > .vscode/settings.json
{
    "python.defaultInterpreterPath": "${PWD}/.venv/bin/python",
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
EOF
    # 4. 🚀 Setup bump (auto-tag releases)
    cat <<EOF >> pyproject.toml
[tool.bumpversion]
current_version = "0.1.0"
commit = true
tag = true
commit_args = "-m 'chore: bump version from {current_version} to {new_version}'"
[[tool.bumpversion.files]]
filename = "pyproject.toml"
search = 'version = "{current_version}"'
replace = 'version = "{new_version}"'
EOF
    # 5. Create .envrc for direnv with auto-activation
    echo "source .venv/bin/activate" > .envrc && direnv allow
    # 6. Initialize Git and fetch a modern .gitignore
    [[ ! -d ".git" ]] && git init && curl -s https://www.toptal.com/developers/gitignore/api/python,linux,vscode > .gitignore
    cat <<EOF >> .gitignore
# insert by 'Luxurious Python Stack'
# volatile, agent-generated data
SESSION.md
plans/
# freestyle: here you can put whatever you want
ignore/
ign/
ignored/
ignored.txt
ingored.md
# end of 'Luxurious Python Stack'    
EOF
    # 7. Final Sync & Success message
    uv sync && echo -e "\e[32m✨ Success! Project '$(basename "$PWD")' is ready.\e[0m"
} # end pyinit
```

```shell
alias pypurge='pip cache purge; mamba clean --all'
```


### Insert in .bashrc

```shell
# direnv hook (MUST BE AT THE END)
eval "$(direnv hook bash)"
```

```shell
# replace generated activation in .bashrc with this
mamba activate $([[ -f ~/.startenv ]] && cat ~/.startenv || echo base)
```

```shell
# optional:
EMOJIS=(🐧 🤐 🥴 🤢 🤮 🤧 😷 🤒 🤕 🤑 🤠 😈 👿 👹 👺 🤡 💩 👻 💀 ☠️ 👽 👾 🤖 🎃 😺 😸 😹 😻 )
RANDOM_EMOJI() { echo "${EMOJIS[$RANDOM % ${#EMOJIS[@]}]}"; }
python_info() {
    if [[ -n "$VIRTUAL_ENV" || -d "./.venv" ]]; then
        echo -e "\033[1;31m(\033[1;36m$(basename "$PWD")\033[1;31m)\033[0m"
    elif [[ -n "$CONDA_DEFAULT_ENV" ]]; then
        echo -e "\033[1;32m(\033[1;34m$CONDA_DEFAULT_ENV\033[1;32m)\033[0m"
    fi
}
# My smart PS1: shows random emoji, user@host, current folder, python env info
export VIRTUAL_ENV_DISABLE_PROMPT=1; prompt_user=$(whoami); prompt_host=$(hostname)
PS1='$(RANDOM_EMOJI) \[\033[1;32m\]╭──(\[\033[1;34m\]${prompt_user}@${prompt_host}\[\033[1;32m\])─[\[\033[1;37m\]\w\[\033[1;32m\]] $(python_info)
\[\033[1;32m\]╰─\[\033[1;34m\]\$\[\033[0m\] '
```

### Data Science Environment (example)

```shell
#                     (re)create a data science environment with all the goodies and activate it
# _________________________________________________________________________________________________________________________________
py=3.12 && ENV_NAME="ds${py: -2}" && mamba deactivate && mamba remove -y -n $ENV_NAME --all 2>/dev/null # python 3.XY --> 'dsXY'
mamba   create -y -n $ENV_NAME python=$py google-colab uv pytorch torchvision torchaudio tensorflow scikit-learn jax \
        -c pytorch -c conda-forge && mamba activate $ENV_NAME
uv pip  install -U jupyterlab jupyter_http_over_ws jupyter-ai[all] jupyterlab-github xeus-python shell-gpt llama-index langchain \
        langchain-ollama langchain-openai langchain-community transformers[torch] evaluate accelerate google-genai nltk tf-keras \
        rouge_score huggingface-hub datasets unstructured[all-docs] jupytext hrid fastai opencv-python soundfile nbdev vllm \
        ollama setuptools wheel graphviz mcp PyPDF2 ipywidgets click==8.1.3 # ⚠️ Use ipywidgets==7.7.1 for Python < 3.12
jupyter labextension enable jupyter_http_over_ws && echo $ENV_NAME > ~/.startenv
python  -m ipykernel install --user --name $ENV_NAME --display-name $ENV_NAME
# _____________________________insert_in_.bashrc_and_use_'act'_instead_of_'mamba_activate'_________________________________________
# mamba activate $(cat ~/.startenv)
# act() { [ "$#" -ne 0 ] && echo $1 > .startenv && mamba activate $1; }
```



## 🧑‍💻 <font color=blue><b>The Daily Workflow</b></font>

### **A handful of fundamental concepts and considerations**

* **`uv run` vs. `direnv`**<br>
The luxury Python stack uses `direnv`. This theoretically eliminates the need for `uv run` when executing commands in the terminal. However, it's important to note that `direnv` just activates the environment, while `uv run` automatically triggers a dependency sync if things have changed (e.g., after a `git pull`).<br>
> **Recommendation:** Always use `uv run` in scripts, aliases, and CI/CD pipelines to guarantee 100% reproducibility. In everyday local terminal use, you can safely omit it to save keystrokes. If module errors arise, simply run `uv sync`.

* **Dev & Release**<br>
A project generally exists in two states: development and release. These are the most important differences:
  * **Dev State:** Your everyday working mode. The code is fluid, and you rely heavily on your dev-dependencies (`pytest`, `ruff`, `mypy`). The version in your `pyproject.toml` remains static while you build features.
  * **Release State:** A frozen, stable snapshot in time. The version number is officially incremented, and a Git tag (e.g., `v0.2.0`) marks the exact commit. This is the state that CI/CD pipelines expect in order to build, test, and deploy your code reliably.

* **Bump a Release (`bump-my-version`)**<br>
Releasing a new version requires keeping the code version (in `pyproject.toml`) and the Git tags perfectly synchronized. Doing this manually (editing the file, committing, and tagging) is highly error-prone and can easily break CI/CD pipelines.<br>
> **Recommendation:** Never edit the version or create tags manually. Use `bump-my-version` to automatically update the configuration, create a clean commit, and set the Git tag in one atomic step. <br>
> **Workflow:** When a feature or bugfix is ready, run `uv run bump-my-version [patch|minor|major]`. Afterwards, push the code and the new tag to your remote repository via `git push origin main --tags`.
---

### **Daily Usecases**

**1. Dependencies & Environment**
* Add package: `uv add <package>`
* Add dev tool: `uv add --dev <package>`
* Sync environment: `uv sync`

**2. Execution & Testing**
* Run code: `python src/my_project/main.py`
* Run tests: `pytest`

**3. Code Quality**
* Linting (find errors): `ruff check .`
* Linting (auto-fix): `ruff check --fix .`
* Type checking: `mypy src/`

**4. Release & Deployment**
* **Bump Version (Git Commit & Tag):**
  * Patch (Bugfixes, e.g., 0.2.0 -> 0.2.1): `uv run bump-my-version patch`
  * Minor (Features, e.g., 0.2.1 -> 0.3.0): `uv run bump-my-version minor`
* **Sync to Remote:**
  * Push code and tags: `git push origin main --tags`
* **Package & Publish (If not handled by CI/CD):**
  * Build the package (creates `dist/`): `uv build`
  * Upload to PyPI / Registry: `uv publish`
