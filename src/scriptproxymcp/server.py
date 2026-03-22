from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from scriptproxymcp.scriptexecute import create_tool_function
from scriptproxymcp.scriptfolder import ScriptFolder

# Basic configuration (once in the script)
logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s - %(name)s [%(module)s.%(funcName)s:%(lineno)d] - "
        "%(levelname)s - %(message)s"
    ),
)

logger = logging.getLogger("MCPScriptProxy")

# Default scripts folder
DEFAULT_SCRIPTS_FOLDER = "./demo/arithmeticmcp"


def get_scripts_folder() -> str:
    """Get the scripts folder from CLI args or environment variable.

    Priority:
    1. CLI positional argument (first argument)
    2. CLI --scripts-folder argument
    3. SCRIPTS_FOLDER environment variable
    4. Default value

    Returns:
        Path to the scripts folder
    """
    parser = argparse.ArgumentParser(
        description="MCP server that exposes bash scripts as tools",
        add_help=False,
    )
    parser.add_argument(
        "scripts_folder",
        nargs="?",
        default=None,
        help="Path to the folder containing scripts",
    )
    parser.add_argument(
        "--scripts-folder",
        dest="scripts_folder_arg",
        default=None,
        help="Path to the folder containing scripts",
    )

    # Parse known args to avoid interfering with FastMCP's argument parsing
    known, _ = parser.parse_known_args()

    # Determine scripts folder with priority
    folder = (
        known.scripts_folder
        or known.scripts_folder_arg
        or os.environ.get("SCRIPTS_FOLDER")
        or DEFAULT_SCRIPTS_FOLDER
    )

    return folder


class MCPScriptProxy:
    """MCP server that exposes bash scripts as MCP tools."""

    def __init__(self, scripts_folder: str | None = None) -> None:
        self.mcp = None  # FastMCP("ScriptProxyMCP")
        scripts_path = scripts_folder or get_scripts_folder()
        # Convert to absolute path for reliable subprocess execution
        self.scripts_folder_path = (
            Path(scripts_path).resolve()
            if not Path(scripts_path).is_absolute()
            else scripts_path
        )

    def scan_folders(self) -> None:
        """Register built-in arithmetic tools with the MCP server."""

        logger.info(f"Scanning scripts folder: {self.scripts_folder_path}")
        self.scripts_folder = ScriptFolder(self.scripts_folder_path)
        self.scripts_folder.scan()

        if self.scripts_folder.isValid:
            n_tools = len(self.scripts_folder.scripts)
            logger.info(f"Found valid folder with {n_tools} tools")
        else:
            logger.info("Scripts folder is invalid")

    def run(self) -> None:
        """Run the MCP server."""
        if not self.scripts_folder.isValid:
            return

        logger.info("Building MCP server...")
        self.mcp = FastMCP("ScriptProxyMCP")
        # create tool for each script
        for script in self.scripts_folder.scripts:
            tool_func = create_tool_function(script)
            self.mcp.add_tool(
                tool_func,
                name=script.tool_name,
                description=script.description,
            )
            logger.info(f"Registered tool: {script.tool_name}")


if __name__ == "__main__":
    scripts_folder = get_scripts_folder()
    server = MCPScriptProxy(scripts_folder)
    server.scan_folders()
    server.run()
    if server.mcp is None:
        raise RuntimeError("Failed to initialize MCP server")
    server.mcp.run()
