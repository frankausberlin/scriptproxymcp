# Script Proxy MCP

ScriptProxyMCP is an MCP (Model Context Protocol) server that turns local scripts into MCP tools.

## What it does

- **Scripts as Tools:** Scans a folder recursively for `.sh` files with `#mcp@` metadata and registers them as MCP tools.
- **Skills as Resources:** Scans subfolders for `SKILL.md` and exposes them as MCP resources.
- **Prompts:** Scans for `.prompt` files to expose as MCP prompts.
- Runs over STDIO, so it can be used directly by MCP clients and the MCP Inspector

## Architecture

```
<server_folder>/
├── mcpproxy.md              # Required server configuration
├── *.sh                     # MCP tools (if #mcp@ metadata present)
├── *.prompt                 # MCP prompts
└── <skill_folder>/
    └── SKILL.md             # Skill (exposed as resource)
```

- **Folder name** = Server name
- **mcpproxy.md** = Server description (required)
- **\*.sh** (recursive) = Tools with `#mcp@name:`, `#mcp@description:`, `#mcp@param:` metadata
- **Subfolders with SKILL.md** = Skills (exposed as resources at `skills://<skill_name>/...`)
- **\*.prompt files** = Prompts

## Requirements

- Python 3.12+
- `uv`
- Bash for shell-based demo scripts

## Local development

Install dependencies once:

```bash
uv sync
```

Run the server from the project directory:

```bash
uv run scriptproxymcp ./demo
```

The server accepts a positional argument or `--server-folder`:

```bash
uv run scriptproxymcp ./demo
uv run scriptproxymcp --server-folder ./demo
```

Environment variable `SERVER_FOLDER` is also supported:

```bash
SERVER_FOLDER=./demo uv run scriptproxymcp
```

### Script Metadata

Scripts need `#mcp@` comments to be registered as tools:

```bash
#!/bin/bash
#mcp@name: add
#mcp@description: Add two numbers
#mcp@param: a: number
#mcp@param: b: number
```

### Skills as Resources

Skills are subfolders containing a `SKILL.md` file. They are exposed as MCP resources:

```
skills://<skill_name>/SKILL.md     → Main SKILL.md file
skills://<skill_name>/<subpath>   → Any file within the skill folder
```

Within skill folders, the server scans the `scripts/` subfolder for `.sh` files with `#mcp@` metadata. These scripts are registered as MCP tools with a `{skill_name}_{script_name}` naming convention.

## MCP Inspector

If you want to test the server manually with the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector uv run scriptproxymcp ./demo
```

## Two operation modes

### Development mode (local checkout)

Use this while actively working on the repository.

```json
{
  "command": "uv",
  "args": ["run", "--directory", "/path/to/project", "scriptproxymcp", "/path/to/server"]
}
```

- **Use case:** active development
- **Behavior:** uses the local checkout
- **Benefit:** code changes are picked up immediately

### Production mode (published package)

Use this when the package is published and no local checkout is needed.

```json
{
  "command": "uvx",
  "args": ["scriptproxymcp", "/path/to/server"]
}
```

- **Use case:** installed release usage
- **Behavior:** downloads and runs the published package
- **Benefit:** simple setup for end users

## Release workflow

This project uses `bump-my-version` for releases.

### Important rule

Do **not** edit the version manually in [`pyproject.toml`](pyproject.toml).

Why:

- [`[project].version`](pyproject.toml:1) and [`[tool.bumpversion].current_version`](pyproject.toml:28) must stay in sync
- the Git commit and the Git tag must match the same release point
- manual edits are easy to forget and easy to break

### Normal release flow

If your working tree is clean, use one of these commands:

```bash
uv run bump-my-version bump patch
uv run bump-my-version bump minor
uv run bump-my-version bump major
```

Example:

```bash
uv run bump-my-version bump minor
```

That will:

1. update the version in [`pyproject.toml`](pyproject.toml)
2. create a release commit
3. create a Git tag such as `v0.4.0` if your tag configuration uses that format

After that, push both the branch and the tag:

```bash
git push
git push --tags
```

### What a clean working tree means

Before running `bump-my-version`, `git status` should look like this:

```bash
git status
```

Expected result:

```text
nothing to commit, working tree clean
```

If there are already modified files, `bump-my-version` may abort because it wants to create a clean, predictable release commit.

### Why two GitHub Actions run after a release

After a successful release you usually push two things:

1. the new commit on [`master`](.github/workflows/ci.yml:5)
2. the new tag like `v0.3.0` matched by [`v*`](.github/workflows/release.yml:7)

That triggers two workflows:

- [`Luxurious CI`](.github/workflows/ci.yml:1) runs for the branch push
- [`Publish Release`](.github/workflows/release.yml:1) runs for the tag push

This is expected behavior.

## Troubleshooting

### `Git working directory is not clean`

Cause:

- you already have local changes
- or a previous failed bump left modified files behind

Fix:

1. inspect with `git status`
2. either commit the unrelated work first
3. or discard the accidental partial bump changes
4. then rerun `bump-my-version`

### `git commit` fails during `bump-my-version`

Check the bump configuration in [`pyproject.toml`](pyproject.toml:28).

Use:

```toml
message = "chore: bump version from {current_version} to {new_version}"
```

Do **not** use a `commit_args` value that injects another `-m`, because `bump-my-version` already builds the commit command itself.
