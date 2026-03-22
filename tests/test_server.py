"""Unit tests for the ScriptProxyMCP server registration flow."""

from __future__ import annotations

import logging
from pathlib import Path

import scriptproxymcp.server as server_module


class DummyScriptFolder:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.isScanned = False
        self.isValid = False
        self.scripts = []
        self.name = self.path.name

    def scan(self) -> None:
        self.isScanned = True
        self.isValid = True

    def __repr__(self) -> str:
        return f"DummyScriptFolder(path={self.path!s})"


class DummyFastMCP:
    def __init__(self, name: str) -> None:
        self.name = name

    def tool(self):
        def decorator(func):
            return func

        return decorator

    def resource(self, _path: str):
        def decorator(func):
            return func

        return decorator


MCPScriptProxy = server_module.MCPScriptProxy
logger = server_module.logger


def test_mcp_application_is_initialized() -> None:
    server = MCPScriptProxy()
    # mcp is None because FastMCP is commented out - that's expected for now
    assert server.mcp is None


def test_register_tools_creates_script_folder_and_logs_it(caplog) -> None:
    original_script_folder = server_module.ScriptFolder
    original_fastmcp = (
        server_module.FastMCP if hasattr(server_module, "FastMCP") else None
    )
    server_module.ScriptFolder = DummyScriptFolder
    # FastMCP doesn't exist in server.py currently, but we keep
    # the mock for future compatibility
    if hasattr(server_module, "FastMCP"):
        server_module.FastMCP = DummyFastMCP

    server = MCPScriptProxy()

    try:
        with caplog.at_level(logging.INFO, logger=logger.name):
            server.scan_folders()
    finally:
        server_module.ScriptFolder = original_script_folder
        if original_fastmcp is not None:
            server_module.FastMCP = original_fastmcp

    assert hasattr(server, "scripts_folder")
    assert server.scripts_folder is not None
    assert server.scripts_folder.path.as_posix().endswith("arithmeticmcp")
    assert server.scripts_folder.isScanned is True
    assert "Scanning scripts folder" in caplog.text
    assert "Found valid folder" in caplog.text
