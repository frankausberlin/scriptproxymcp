# Script Proxy MCP

An MCP (Model Context Protocol) server that makes Bash scripts available as MCP tools and exposes skills as MCP resources.

## Features

- **Automatic Detection**: Scans the `scripts/` directory for `.sh` files.


## Run the server locally

The server runs over STDIO by default.

```bash
uv run src/scriptproxymcp/server.py
```

## Requirements

- Python 3.12+
- `mcp` package (Model Context Protocol)
- Bash shell

## Use it with MCP Inspector

For the MCP Inspector, use the Python/STDIO setup described in the official docs:

- Command: `uv [--directory <path-to-project>] run src/scriptproxymcp/server.py`

In the Inspector, that maps to the command and arguments fields in the STDIO connection pane.

If you launch the Inspector directly from the project directory, the equivalent command is:

```bash
npx @modelcontextprotocol/inspector uv run src/scriptproxymcp/server.py
```

