# 🤖 Agent Guide: ScriptProxyMCP

## 🎯 Project goal
This package serves as an MCP server proxy to provide local scripts (Python, Bash, etc.) as tools for LLMs. Focus is on simplicity and security.

## 🏗️ Architecture & Conventions
- **Core Logic:** Located in `src/scriptproxymcp/`.
- **Module structure:** `scriptfolder.py` (scanning) and `scriptexecute.py` (execution).
- **Import style:** We use the `__init__.py` as a facade. External imports should run via the main package.
- **Typing:** Strict type hinting is desired (Mypy compatible).

## 🛠️ Tooling (information level)
- **Package manager:** The project uses `uv`. For dependencies please use `uv add`.
- **Quality:** `ruff` for linting/formatting, `mypy` for types, `pytest` for tests.
- **Versioning:** `bump-my-version` is used for releases. **Never change versions manually in `pyproject.toml`** - doing so causes version inconsistencies between `[project].version` and `[tool.bumpversion].current_version`.

## 📜 Best practices for this repo
1. **New tools:** When a new script execution feature is added, the tool definition in `scriptexecute.py` must be dynamically generated.
2. **Security:** Script calls must be made via `subprocess` with validated arguments.
3. **Documentation:** Functions require Google-style docstrings, as these often serve as the basis for the MCP tool descriptions.

## 🚩 Known limitations/roadmap
- Currently only support for Python and shell scripts.
- Sandboxing of the subprocesses is still being planned.

## 🧑‍💻 Workflow
1. **SESSION.md** is a volatile file that contains the **summary of the last session**.
2. Read the “SESSION.md” at the beginning of each task to get the summary of the last session.
3. When completing a task, write a new "SESSION.md" file with a **new summary** of the current session.

## 🧑‍🔧 Troubleshooting
- If tests are failing, check the error messages carefully. They often indicate which function or module is causing the issue.
- For import errors, ensure that you are importing from the main package and not directly from submodules.
- If you encounter issues with subprocess calls, verify that the arguments are properly validated and that the scripts being called exist in the expected locations.