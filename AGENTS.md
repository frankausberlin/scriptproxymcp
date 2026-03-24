# 🤖 Agent Guide: ScriptProxyMCP

## 🎯 Project goal
This package serves as an MCP server proxy to provide local scripts (Python, Bash, etc.) as tools for LLMs. Focus is on simplicity and security.

## 🏗️ Architecture & Conventions
- **Core Logic:** Located in `src/scriptproxymcp/`.
- **Module structure:**
  - `scriptfolder.py` - scanning for scripts (ScriptFolder class)
  - `skillfolder.py` - scanning for skills (SkillFolder class)
  - `scriptexecute.py` - script execution
  - `datatypes.py` - type definitions (ScriptInfo, SkillInfo)
- **Import style:** We use the `__init__.py` as a facade. External imports should run via the main package.
- **Typing:** Strict type hinting is desired (Mypy compatible).

## 🛠️ Tooling (information level)
- **Package manager:** The project uses `uv`. For dependencies please use `uv add`.
- **Quality:** `ruff` for linting/formatting, `mypy` for types, `pytest` for tests.
- **Versioning:** `bump-my-version` is used for releases. **Never change versions manually in `pyproject.toml`** - doing so causes version inconsistencies between `[project].version` and `[tool.bumpversion].current_version`.
- **bump-my-version config:** Use `message = "..."` in `[tool.bumpversion]`. Do **not** use `commit_args = "-m ..."`, because `bump-my-version` already manages the commit message internally and this can break release commits.

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
4. For releases, prefer a clean working tree and use `uv run bump-my-version bump <patch|minor|major>` instead of editing versions by hand.

## 🧑‍🔧 Troubleshooting
- If tests are failing, check the error messages carefully. They often indicate which function or module is causing the issue.
- For import errors, ensure that you are importing from the main package and not directly from submodules.
- If you encounter issues with subprocess calls, verify that the arguments are properly validated and that the scripts being called exist in the expected locations.
