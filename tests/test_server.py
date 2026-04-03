"""Tests for MCPScriptProxy server."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from scriptproxymcp.server import (
    DEFAULT_SERVER_FOLDER,
    MCP_PROXY_CONFIG,
    MCPScriptProxy,
)


class TestMCPScriptProxyInit:
    """Tests for MCPScriptProxy initialization."""

    def test_default_folder_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test default folder path uses get_server_folder when no folder provided."""
        from scriptproxymcp.server import MCPScriptProxy

        # Mock get_server_folder to return a known path
        expected_path = "/fake/test/path"
        monkeypatch.setattr(MCPScriptProxy, "get_server_folder", lambda: expected_path)

        server = MCPScriptProxy()
        assert str(server.folder_path) == expected_path

    def test_default_folder_is_module_relative(self) -> None:
        """DEFAULT_SERVER_FOLDER must be module-relative, not CWD-relative.

        Regression guard: changing CWD must not affect the default path.
        """
        import scriptproxymcp.server as server_module

        default = Path(DEFAULT_SERVER_FOLDER)
        # The default path must be derived from the module file location,
        # not from the current working directory.
        module_root = Path(server_module.__file__).parent.parent.parent
        assert default == module_root / "demo" / "arithmeticmcp", (
            "DEFAULT_SERVER_FOLDER must be relative to the module, not CWD"
        )

        # Verify the path stays stable even when CWD changes.
        with tempfile.TemporaryDirectory() as tmp:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmp)
                assert Path(DEFAULT_SERVER_FOLDER) == default
            finally:
                os.chdir(original_cwd)

    def test_custom_folder_path(self, tmp_path: Path) -> None:
        """Test that custom folder path is set correctly."""
        server = MCPScriptProxy(str(tmp_path))
        assert str(server.folder_path) == str(tmp_path.resolve())

    def test_relative_path_resolution(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that relative paths starting with ./ or ../ are resolved relative to script dir."""
        # Change to a different directory to simulate MCP Inspector scenario
        with tempfile.TemporaryDirectory() as tmp_cwd:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmp_cwd)

                # Create a relative path that should be resolved relative to script dir
                script_dir = Path(__file__).parent.parent
                demo_dir = script_dir / "demo" / "ubuntuadminmcp"

                # Mock the script directory resolution
                server = MCPScriptProxy("./demo/ubuntuadminmcp")
                assert str(server.folder_path) == str(demo_dir.resolve())

            finally:
                os.chdir(original_cwd)

    def test_initial_collections(self, tmp_path: Path) -> None:
        """Test that collections are initialized empty."""
        server = MCPScriptProxy(str(tmp_path))
        assert server.scripts == []
        assert server.skills == []
        assert server.prompts == []
        assert server.server_info is None


class TestReadMcpproxyMd:
    """Tests for _read_mcpproxy_md method."""

    def test_missing_config_file(self, tmp_path: Path) -> None:
        """Test that missing mcpproxy.md returns None."""
        server = MCPScriptProxy(str(tmp_path))
        result = server._read_mcpproxy_md()
        assert result is None

    def test_valid_config_file(self, tmp_path: Path) -> None:
        """Test reading valid mcpproxy.md file."""
        config_content = "# My Server\nThis is a test server."
        (tmp_path / MCP_PROXY_CONFIG).write_text(config_content)

        server = MCPScriptProxy(str(tmp_path))
        result = server._read_mcpproxy_md()

        assert result is not None
        assert result.name == tmp_path.name
        assert "test server" in result.description.lower()

    def test_config_name_from_folder(self, tmp_path: Path) -> None:
        """Test that server name comes from folder name."""
        (tmp_path / MCP_PROXY_CONFIG).write_text("Server description here.")

        server = MCPScriptProxy(str(tmp_path))
        result = server._read_mcpproxy_md()

        assert result is not None
        assert result.name == tmp_path.name


class TestParseScript:
    """Tests for _parse_script method."""

    def test_valid_script(self, tmp_path: Path) -> None:
        """Test parsing a valid script with full metadata."""
        script_content = """#!/bin/bash
#mcp@name: add
#mcp@description: Add two numbers
#mcp@param: a: number
#mcp@param: b: number
echo $((a + b))
"""
        script_path = tmp_path / "add.sh"
        script_path.write_text(script_content)

        server = MCPScriptProxy(str(tmp_path))
        result = server._parse_script(script_path)

        assert result is not None
        assert result.tool_name == "add"
        assert result.description == "Add two numbers"
        assert len(result.params) == 2

    def test_missing_name_returns_none(self, tmp_path: Path) -> None:
        """Test that script without name returns None."""
        script_content = """#!/bin/bash
#mcp@description: No name here
echo "test"
"""
        script_path = tmp_path / "test.sh"
        script_path.write_text(script_content)

        server = MCPScriptProxy(str(tmp_path))
        result = server._parse_script(script_path)

        assert result is None

    def test_missing_description_returns_none(self, tmp_path: Path) -> None:
        """Test that script without description returns None."""
        script_content = """#!/bin/bash
#mcp@name: test
echo "test"
"""
        script_path = tmp_path / "test.sh"
        script_path.write_text(script_content)

        server = MCPScriptProxy(str(tmp_path))
        result = server._parse_script(script_path)

        assert result is None

    def test_params_parsing(self, tmp_path: Path) -> None:
        """Test that parameters are parsed correctly."""
        script_content = """#!/bin/bash
#mcp@name: calc
#mcp@description: Calculator
#mcp@param: x: int
#mcp@param: y: float
#mcp@param: operation: string
"""
        script_path = tmp_path / "calc.sh"
        script_path.write_text(script_content)

        server = MCPScriptProxy(str(tmp_path))
        result = server._parse_script(script_path)

        assert result is not None
        assert len(result.params) == 3
        assert result.params[0] == {"name": "x", "type": "int"}
        assert result.params[2] == {"name": "operation", "type": "string"}


class TestScanScripts:
    """Tests for _scan_scripts method."""

    def test_finds_scripts_recursively(self, tmp_path: Path) -> None:
        """Test that scripts are found recursively."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        (tmp_path / "script1.sh").write_text("#mcp@name: s1\n#mcp@description: Script 1\n")
        (subdir / "script2.sh").write_text("#mcp@name: s2\n#mcp@description: Script 2\n")

        server = MCPScriptProxy(str(tmp_path))
        scripts = server._scan_scripts()

        assert len(scripts) == 2
        tool_names = {s.tool_name for s in scripts}
        assert "s1" in tool_names
        assert "s2" in tool_names

    def test_ignores_scripts_without_metadata(self, tmp_path: Path) -> None:
        """Test that scripts without #mcp@ metadata are ignored."""
        (tmp_path / "valid.sh").write_text("#mcp@name: valid\n#mcp@description: Valid\n")
        content = "# Just a comment\n"
        content += "echo 'no metadata'"
        (tmp_path / "invalid.sh").write_text(content)

        server = MCPScriptProxy(str(tmp_path))
        scripts = server._scan_scripts()

        assert len(scripts) == 1
        assert scripts[0].tool_name == "valid"


class TestScanSkills:
    """Tests for _scan_skills method."""

    def test_finds_skill_folders(self, tmp_path: Path) -> None:
        """Test that skill folders are found."""
        skill_dir = tmp_path / "my_skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: my-skill\ndescription: Test skill\n---\n# My Skill")

        server = MCPScriptProxy(str(tmp_path))
        skills = server._scan_skills()

        assert len(skills) == 1
        assert skills[0].name == "my-skill"

    def test_ignores_folders_without_skill_md(self, tmp_path: Path) -> None:
        """Test that folders without SKILL.md are ignored."""
        (tmp_path / "skill").mkdir()
        not_skill = tmp_path / "not_a_skill"
        not_skill.mkdir()
        (not_skill / "README.md").write_text("Not a skill")

        server = MCPScriptProxy(str(tmp_path))
        skills = server._scan_skills()

        assert len(skills) == 0

    def test_skill_with_scripts(self, tmp_path: Path) -> None:
        """Test that skill scripts are collected."""
        skill_dir = tmp_path / "test_skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: test\n---\n# Test")
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "helper.sh").write_text("#mcp@name: help\n#mcp@description: Help\n")

        server = MCPScriptProxy(str(tmp_path))
        skills = server._scan_skills()

        assert len(skills) == 1
        assert len(skills[0].scripts) == 1
        assert skills[0].scripts[0].tool_name == "help"


class TestScanPrompts:
    """Tests for _scan_prompts method."""

    def test_finds_prompt_files(self, tmp_path: Path) -> None:
        """Test that .prompt files are found."""
        (tmp_path / "test.prompt").write_text("Hello {name}!")
        (tmp_path / "other.prompt").write_text("Another prompt")

        server = MCPScriptProxy(str(tmp_path))
        prompts = server._scan_prompts()

        assert len(prompts) == 2

    def test_parse_json_prompt(self, tmp_path: Path) -> None:
        """Test parsing JSON format prompt."""
        content = json.dumps(
            {
                "name": "greet",
                "description": "Greet someone",
                "template": {"message": "Hello {name}"},
            }
        )
        (tmp_path / "greet.prompt").write_text(content)

        server = MCPScriptProxy(str(tmp_path))
        prompts = server._scan_prompts()

        assert len(prompts) == 1
        assert prompts[0].name == "greet"
        assert prompts[0].description == "Greet someone"

    def test_parse_text_prompt(self, tmp_path: Path) -> None:
        """Test parsing plain text prompt."""
        (tmp_path / "simple.prompt").write_text("Simple template text")

        server = MCPScriptProxy(str(tmp_path))
        prompts = server._scan_prompts()

        assert len(prompts) == 1
        assert prompts[0].name == "simple"
        assert prompts[0].template == "Simple template text"


class TestScanIntegration:
    """Integration tests for scan method."""

    def test_scan_valid_folder(self, tmp_path: Path) -> None:
        """Test scanning a complete folder structure."""
        (tmp_path / MCP_PROXY_CONFIG).write_text("# Test Server")
        tool_content = "#mcp@name: tool\n#mcp@description: A tool\n"
        (tmp_path / "tool.sh").write_text(tool_content)
        skill_dir = tmp_path / "test_skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: test\n---\n# Test")
        (tmp_path / "test.prompt").write_text("Template")

        server = MCPScriptProxy(str(tmp_path))
        result = server.scan()

        assert result is True
        assert server.server_info is not None
        assert len(server.scripts) == 1
        assert len(server.skills) == 1
        assert len(server.prompts) == 1

    def test_scan_missing_mcpproxy_md(self, tmp_path: Path) -> None:
        """Test that scan fails without mcpproxy.md."""
        server = MCPScriptProxy(str(tmp_path))
        result = server.scan()

        assert result is False
        assert server.server_info is None

    def test_scan_nonexistent_folder(self) -> None:
        """Test that scan fails for nonexistent folder."""
        server = MCPScriptProxy("/nonexistent/path")
        result = server.scan()

        assert result is False
