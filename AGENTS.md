# Agent instructions for scriptproxymcp

## Project batch
- **Manager:** uv (always use “uv run”, “uv add”)
- **Linter/Formatter:** Ruff
- **Test Runner:** pytest

## Coding style and settings
- **Vertical Alignment:** I prefer column-oriented formatting for imports and long lists. 
- **IMPORTANT:** Always wrap these blocks in “# fmt: off” and “# fmt: on” so Ruff doesn't touch them.
- **CI/CD Awareness:** We have a strict GitHub action pipeline. Always run “uv run ruff check” before proposing a commit.
- **Documentation:** Keep it “luxurious” – clean, concise, but with a touch of class in the README.

## Workflow
1. Read the “SESSION.md” at the beginning of each task to get the summary of the last session.
2. When completing a task, write a new "SESSION.md" file with a summary of the current session.

!!!under construction!!!