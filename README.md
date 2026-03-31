# Script Proxy MCP

ScriptProxyMCP is a Model Context Protocol (MCP) server that turns local scripts into MCP tools.

## What it does

- **Folder as server:** Any folder with a `mcpproxy.md` file is treated as an MCP server.
- **Scripts as tools:** The server recursively scans for `.sh` files with `#mcp@` metadata and registers them as MCP tools.
- **Skills as resources:** Subfolders that contain `SKILL.md` are exposed as MCP resources.
- **Prompts:** `.prompt` files are exposed as MCP prompts.
- **STDIO transport:** The server runs directly over STDIO and works with MCP clients and the MCP Inspector.

## Architecture

Each MCP server folder must contain a `mcpproxy.md` file:

```shell
<server_folder>/
├── mcpproxy.md   # required server configuration
├── *.sh          # MCP tools (if #mcp@ metadata exists)
├── *.prompt      # MCP prompts
└── <skill_folder>/
    └── SKILL.md  # skill resource
```

- **folder name** = server name
- **`mcpproxy.md`** = required server description
- **`*.sh`** (recursive) = tools with `#mcp@name`, `#mcp@description`, and `#mcp@param` metadata
- **skill subfolders** = resources under `skills://<skill_name>/...`
- **`*.prompt`** = prompt definitions

## Requirements

- Python 3.12+
- `uv`
- `just`
- Bash for shell-based scripts

## Demo server

This repository includes a demo server under `demo/arithmeticmcp`.

```shell
uv run scriptproxymcp ./demo/arithmeticmcp
```

## Local development

Install or update the environment:

```shell
uv sync
```

Run the stack quality gate:

```shell
just check
```

Run a demo server:

```shell
uv run scriptproxymcp ./demo/arithmeticmcp
uv run scriptproxymcp --server-folder ./demo/arithmeticmcp
SERVER_FOLDER=./demo/arithmeticmcp uv run scriptproxymcp
```

### Daily commands

```shell
just lint       # ruff check + formatting check
just typecheck  # basedpyright
just test       # pytest
just check      # full quality gate
just fix        # auto-fix with ruff
```

### Script metadata

Scripts require `#mcp@` comments to register as tools:

```shell
#!/bin/bash
#mcp@name: add
#mcp@description: Add two numbers
#mcp@param: a: number
#mcp@param: b: number
```

### Skills as resources

Skills are subfolders that contain a `SKILL.md` file. They are exposed as MCP resources:

```text
skills://<skill_name>/SKILL.md
skills://<skill_name>/<subpath>
```

Within skill folders, the server scans `scripts/` for `.sh` files with `#mcp@` metadata. Those scripts are registered as MCP tools using the naming convention `{skill_name}_{script_name}`.

## MCP Inspector

```shell
npx @modelcontextprotocol/inspector uv run scriptproxymcp ./demo/arithmeticmcp
```

## Two operating modes

### Development mode

Use this while actively working on a local checkout.

```json
{
  "command": "uv",
  "args": ["run", "--directory", "/path/to/project", "scriptproxymcp", "/path/to/server"]
}
```

### Production mode

Use this when the package is published and a local checkout is not required.

```json
{
  "command": "uvx",
  "args": ["scriptproxymcp", "/path/to/server"]
}
```

## Release workflow

This project uses `bump-my-version` for semantic versioning.

### Important rule

Do **not** edit the version manually in `pyproject.toml`.

The values in `[project].version` and `[tool.bumpversion].current_version` must stay synchronized.

### Normal release flow

If the working tree is clean, use one of these commands:

```shell
just bump patch
just bump minor
just bump major
```

This updates the version, creates the release commit, and creates the matching Git tag.

Then push the branch and the tags:

```shell
git push origin main
git push origin main --tags
```

### Clean working tree requirement

Before running `bump-my-version`, check:

```shell
git status
```

If there are already modified files, the release may abort to protect the release commit.

### Why two GitHub Actions run after a release

After a successful release, you usually push:

1. the new commit on `main`
2. the new tag that matches `v*`

This triggers both workflows:

- `Luxurious CI` on the branch push
- `Publish Release` on the tag push

That behavior is expected.

### bump-my-version configuration

Use the `message = "..."` setting in `[tool.bumpversion]`.

Do **not** use `commit_args = "-m ..."`, because `bump-my-version` already controls commit creation internally.
