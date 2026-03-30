# Script Proxy MCP

ScriptProxyMCP is a Model Context Protocol (MCP) server that turns local scripts into MCP tools.

## What it does

- **Folder as Server:** Any folder with a “mcpproxy.md” file will be registered as an MCP server.
- **Scripts as tools:** Recursively searches a folder for ".sh" files with "#mcp@" metadata and registers them as MCP tools.
- **Skills as resources:** Searches subfolders for “SKILL.md” and provides them as MCP resources.
- **Prompts:** Searches for .prompt (json) files to display as MCP prompts.
- **Runs via STDIO** and can therefore be used directly by MCP clients and the MCP inspector

## Architecture

Each MCP server folder must contain a mcpproxy.md file:

```shell
<server_folder>/
├── mcpproxy.md # Required server configuration
├── *.sh # MCP tools (if #mcp@ metadata exists)
├── *.prompt # MCP prompts
└── <skill_folder>/
    └── SKILL.md # Skill (exposed as a resource)
```

- **folder name** = server name
- **mcpproxy.md** = Server description (required), first '#' -> short description, remaining content -> long description
- **\*.sh** (recursive) = Tools with "#mcp@name:", "#mcp@description:", "#mcp@param:" metadata
- **Subfolder with SKILL.md** = Skills (made available as resources under "skills://<skill_name>/...")
- **\*.prompt files** = Prompts

## Requirements

- Python 3.12+
- `uv`
- Bash for shell-based scripts

## Demo server

This project includes a demo server:

### Arithmetic MCP server

Provides basic arithmetic operations (addition, subtraction, multiplication, division, power).

```shell
uv run scriptproxymcp ./demo/arithmeticmcp
```


## Local development

Install dependencies once:

```shell
uv sync
```

Run a demo server:

```shell
uv run scriptproxymcp ./demo/arithmeticmcp
```

The server accepts a positional argument or “--server-folder”:

```shell
uv run scriptproxymcp ./demo/arithmeticmcp
uv run scriptproxymcp --server-folder ./demo/arithmeticmcp
```

The environment variable “SERVER_FOLDER” is also supported:

```shell
SERVER_FOLDER=./demo/arithmeticmcp uv run scriptproxymcp
```

### Script metadata

Scripts require #mcp@ comments to register as tools:

```shell
#!/bin/bash
#mcp@name: add
#mcp@description: Add two numbers
#mcp@param: a: number
#mcp@param: b: number
```

### Skills as resources

Skills are subfolders that contain a SKILL.md file. They are provided as MCP resources:

```
skills://<skill_name>/SKILL.md → main file SKILL.md
skills://<skill_name>/<subpath> → Any file in the skills folder
```

Within skill folders, the server searches the scripts/ subfolder for .sh files with #mcp@ metadata. These scripts are registered as MCP tools with the naming convention “{skill_name}_{script_name}”.

## MCP inspector

If you want to test the server manually using the MCP Inspector:

```shell
npx @modelcontextprotocol/inspector uv run scriptproxymcp ./demo/arithmeticmcp
```

## Two operating modes

### Development mode (local checkout)

Use this while you are actively working on the repository.

```json
{
  “command”: “uv”,
  "args": ["run", "--directory", "/path/to/project", "scriptproxymcp", "/path/to/server"]
}
```

- **Use case:** active development
- **Behavior:** uses local checkout
- **Advantage:** Code changes are applied immediately

### Production mode (released package)

Use this when the package is published and local checkout is not required.

```json
{
  “command”: “uvx”,
  “args”: [“scriptproxymcp”, “/path/to/server”]
}
```

- **Use case:** installed release usage
- **Behavior:** downloads and runs the published package
- **Advantage:** Easy setup for end users

## Release workflow

This project uses bump-my-version for publishing.

### Important rule

Do **do not** edit the version manually in [`pyproject.toml`](pyproject.toml).

Why:

- [`[project].version`](pyproject.toml:1) and [`[tool.bumpversion].current_version`](pyproject.toml:28) must remain in sync
– The Git commit and Git tag must match the same release point
- Manual changes are easily forgotten and easily interrupted

### Normal release flow

If your working tree is clean, use one of these commands:

```shell
UV Run Bump My Version Bump Patch
UV Run Bump My Version Bump Minor
UV Run Bump-my version Bump Major
```

Example:

```shell
UV Run Bump My Version Bump Minor
```

This will:

1. Update the version in [`pyproject.toml`](pyproject.toml)
2. Create a release commit
3. Create a Git tag like “v0.4.0” if your tag configuration uses this format

Then push both the branch and the tag:

```shell
Git push
git push --tags
```

### What a clean working tree means

Before running bump-my-version, git status should look like this:

```shell
Git status
```

Expected result:

```
There is nothing to commit to cleaning the tree
```

If there are already changed files, bump-my-version may abort because it wants to create a clean, predictable release commit.

### Why two GitHub actions are executed after a publish

After a successful release, you typically push two things:

1. the new commit on [`master`](.github/workflows/ci.yml:5)
2. the new tag like “v0.3.0”, matching [`v*`](.github/workflows/release.yml:7)

This triggers two workflows:

- [`Luxurious CI`](.github/workflows/ci.yml:1) is running for branch push
- [`Publish Release`](.github/workflows/release.yml:1) is executed for tag push

This is expected behavior.

## Bug fix

### "Git working directory is not clean".

Cause:

- You have already made local changes
- or a previous failed push left behind modified files

Fix:

1. Check with “git status”.
2. Either do the independent work first
3. or discard the accidental partial bump changes
4. Then run “bump-my-version” again

### git commit fails during bump-my-version

Check the bump configuration in [`pyproject.toml`](pyproject.toml:28).

Usage:

“Toml
message = “Task: Increase version from {current_version} to {new_version}”
“

Don't **use** a commit_args value that inserts another "-m" because bump-my-version already creates the commit command itself.