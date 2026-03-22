"""Unit tests for the server module functions."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from scriptproxymcp.server import (
    DEFAULT_SCRIPTS_FOLDER,
    MCPScriptProxy,
    get_scripts_folder,
)


class TestGetScriptsFolder:
    """Tests for get_scripts_folder function."""

    def test_get_scripts_folder_env_var(self) -> None:
        """Test that SCRIPTS_FOLDER environment variable is respected."""
        env_var_value = "/custom/scripts/path"

        with patch.dict(os.environ, {"SCRIPTS_FOLDER": env_var_value}):
            with patch("sys.argv", ["scriptproxymcp"]):
                result = get_scripts_folder()

        assert result == env_var_value

    def test_get_scripts_folder_cli_positional_arg(self) -> None:
        """Test that CLI positional argument takes highest priority."""
        cli_path = "/cli/positional/path"

        with patch.dict(os.environ, {"SCRIPTS_FOLDER": "/env/path"}):
            with patch("sys.argv", ["scriptproxymcp", cli_path]):
                result = get_scripts_folder()

        assert result == cli_path

    def test_get_scripts_folder_cli_arg_flag(self) -> None:
        """Test that CLI --scripts-folder flag is respected."""
        cli_path = "/cli/flag/path"

        with patch.dict(os.environ, {"SCRIPTS_FOLDER": "/env/path"}):
            with patch("sys.argv", ["scriptproxymcp", "--scripts-folder", cli_path]):
                result = get_scripts_folder()

        assert result == cli_path

    def test_get_scripts_folder_cli_positional_over_flag(self) -> None:
        """Test that positional arg takes priority over --scripts-folder flag."""
        positional_path = "/positional/path"
        flag_path = "/flag/path"

        with patch(
            "sys.argv",
            ["scriptproxymcp", positional_path, "--scripts-folder", flag_path],
        ):
            result = get_scripts_folder()

        assert result == positional_path

    def test_get_scripts_folder_default(self) -> None:
        """Test that default fallback is used when no env var or CLI args."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("sys.argv", ["scriptproxymcp"]):
                result = get_scripts_folder()

        assert result == DEFAULT_SCRIPTS_FOLDER

    def test_get_scripts_folder_env_var_over_default(self) -> None:
        """Test that env var takes priority over default."""
        env_path = "/env/override/path"

        with patch.dict(os.environ, {"SCRIPTS_FOLDER": env_path}):
            with patch("sys.argv", ["scriptproxymcp"]):
                result = get_scripts_folder()

        assert result == env_path


class TestMCPScriptProxy:
    """Tests for MCPScriptProxy class."""

    def test_absolute_path_conversion(self) -> None:
        """Verify that relative paths are converted to absolute paths."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("sys.argv", ["scriptproxymcp", "./demo/arithmeticmcp"]):
                proxy = MCPScriptProxy()

        resolved_path = Path("./demo/arithmeticmcp").resolve()
        assert proxy.scripts_folder_path == resolved_path

    def test_absolute_path_unchanged(self) -> None:
        """Verify that absolute paths remain unchanged (not converted to absolute again)."""
        absolute_path = "/absolute/path/to/scripts"

        with patch.dict(os.environ, {}, clear=True):
            with patch("sys.argv", ["scriptproxymcp"]):
                proxy = MCPScriptProxy(scripts_folder=absolute_path)

        # When an absolute path is provided, it stays as-is (not wrapped in Path)
        # The server.py code: Path(scripts_path).resolve() if not is_absolute else scripts_path
        assert proxy.scripts_folder_path == absolute_path

    def test_scripts_folder_path_is_path_object(self) -> None:
        """Verify scripts_folder_path is a Path object."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("sys.argv", ["scriptproxymcp"]):
                proxy = MCPScriptProxy()

        assert isinstance(proxy.scripts_folder_path, Path)

    def test_mcp_attribute_initialized_to_none(self) -> None:
        """Verify mcp attribute is None on initialization."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("sys.argv", ["scriptproxymcp"]):
                proxy = MCPScriptProxy()

        assert proxy.mcp is None

    def test_scan_folders_creates_scripts_folder(self) -> None:
        """Verify scan_folders creates the scripts_folder attribute."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("sys.argv", ["scriptproxymcp", "./demo/arithmeticmcp"]):
                proxy = MCPScriptProxy()

        proxy.scan_folders()

        assert hasattr(proxy, "scripts_folder")
        assert proxy.scripts_folder is not None
        assert proxy.scripts_folder.isScanned is True

    def test_scan_folders_detects_valid_folder(self) -> None:
        """Verify scan_folders correctly identifies a valid scripts folder."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("sys.argv", ["scriptproxymcp", "./demo/arithmeticmcp"]):
                proxy = MCPScriptProxy()

        proxy.scan_folders()

        assert proxy.scripts_folder.isValid is True
        assert len(proxy.scripts_folder.scripts) > 0

    def test_scan_folders_detects_invalid_folder(self, tmp_path: Path) -> None:
        """Verify scan_folders correctly identifies an invalid scripts folder."""
        # Create an empty folder (no scripts with MCP metadata)
        empty_folder = tmp_path / "empty"
        empty_folder.mkdir()

        with patch.dict(os.environ, {}, clear=True):
            with patch("sys.argv", ["scriptproxymcp"]):
                proxy = MCPScriptProxy(scripts_folder=str(empty_folder))

        proxy.scan_folders()

        assert proxy.scripts_folder.isScanned is True
        assert proxy.scripts_folder.isValid is False
        assert len(proxy.scripts_folder.scripts) == 0
