"""ScriptProxyMCP - A Python package for running scripts as an MCP server."""

__version__ = "0.3.0"

from .scriptexecute import create_tool_function
from .scriptfolder import ScriptFolder

__all__ = [
    "ScriptFolder",
    "create_tool_function",
]
