This is important information for AI agents.

The following Python stack is used (levels 3 and 4 are under construction):

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

Scripts and Aliases:
- **cw**: `cw` -> change to working folder / `cw .` -> make current folder the working folder.
- **act**: Activates a Mamba environment and saves it in the file ~/.startenv.
- **pyinit**: Creates a Python project with all files and folders (src, tests, pyproject.toml, etc.) and initializes a UV environment.
- **pypurge**: An alias for purging the pip cache and cleaning the Mamba environment.


### Three-level concept

My workflow is based on a five-level concept:

0. **System Level**

* The standard Python is available here (/usr/bin/python).
* Important tools such as git, rg, fd and the build essentials are installed.
* UV, direnv and Mamba are also installed but not set up.
* The system level is automatically active as soon as no other environment is activated.

1. **Data Science Level**

* This level is for data science work and is set up using Mamba.
* It includes tools like Jupyter Lab, pytorch, tensorflow, scikit-learn, and other data science libraries.
* This level is always active if there is no .venv folder in the current location or you deactivate it.
* Using `act` to activate an environment will automatically activate it in new terminals (.startenv).

2. **Project Level**

* This level is intended for folders with .venv, for example for projects.
* As soon as there is a .venv folder in the current folder, it will be automatically activated (direnv).
* With `pyinit` you can quickly create a new project with a .venv folder and have the required files and folders created.
* If you prefer to work with uv venv / init yourself, this is not a problem, as direnv automatically activates .venv

3. **CI / Deployment**

under construction

4. **AI Agents / Vibe Coding**

* **AGENTS.md** ist teil des Repositories. Hier befinden sich relevante Information für einen ki-agenten um das projekt zu verstehen und daran zu arbeiten.
* **xyz.md** (todo: name) ist kein teil des repositories und steht im .gitignore. Es ist eine flüchtige datei die nur der session-übergreifenden kommunikation zwischen agenten ermöglicht.

under construction

⚠️ **Important Note Regarding the "Data Science Level":**<br>
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
    # 1. Create and enter directory (if a name was passed) and uv init it.
    [[ "$_dir" != "." ]] && mkdir -p "$_dir" && cd "$_dir"
    echo -e "\e[34m💎 Initializing $_type project in $(basename "$PWD")...\e[0m"
    # forcing managed Python to avoid mamba conflicts
    export UV_PYTHON_PREFERENCE=only-managed && uv init $_type --python 3.12
    # 2. Add essential Dev-Tools
    uv add --dev ruff pytest mypy
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
    # 4. Create .envrc for direnv with auto-activation
    echo "source .venv/bin/activate" > .envrc && direnv allow
    # 5. Initialize Git and fetch a modern .gitignore
    [[ ! -d ".git" ]] && git init && curl -s https://www.toptal.com/developers/gitignore/api/python,linux,vscode > .gitignore
    # 6. Final Sync & Success message
    uv sync && echo -e "\e[32m✨ Success! Project '$(basename "$PWD")' is ready.\e[0m"
}
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
