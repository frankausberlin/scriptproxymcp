# ScriptProxyMCP

ScriptProxyMCP is a small MCP server that exposes arithmetic tools and a math constants resource using [FastMCP](src/scriptproxymcp/server.py:1).

## Features

- `add(a, b)`
- `subtract(a, b)`
- `multiply(a, b)`
- `divide(a, b)`
- `math/constant/{name}` resource for `pi`, `e`, and `tau`

## Run the server locally

The server runs over STDIO by default.

```bash
uv run src/scriptproxymcp/server.py
```

## Use it with MCP Inspector

For the MCP Inspector, use the Python/STDIO setup described in the official docs:

- Command: `uv`
- Arguments: `--directory /home/frank/labor/gits/scriptproxymcp run src/scriptproxymcp/server.py`

In the Inspector, that maps to the command and arguments fields in the STDIO connection pane.

If you launch the Inspector directly from the project directory, the equivalent command is:

```bash
npx -y @modelcontextprotocol/inspector uv --directory /home/frank/labor/gits/scriptproxymcp run src/scriptproxymcp/server.py
```

## Development

Install dependencies and run checks:

```bash
uv sync
uv run python -m py_compile src/scriptproxymcp/server.py
```
