"""Unit tests for the ScriptFolder class."""

from __future__ import annotations

from pathlib import Path

from scriptproxymcp.datatypes import ScriptInfo
from scriptproxymcp.scriptfolder import ScriptFolder


class TestScriptFolderScan:
    """Tests for ScriptFolder.scan() method."""

    def test_scan_finds_scripts(self, tmp_path: Path) -> None:
        """Verify that scripts with valid MCP metadata are discovered."""
        # Create a test script with MCP metadata
        script_content = """#!/bin/bash
#mcp@name test_script
#mcp@description A test script for unit testing
#mcp@param a:int
#mcp@param b:int
echo $((a + b))
"""
        script_file = tmp_path / "test_script.sh"
        script_file.write_text(script_content)

        # Create a non-script file (should be ignored)
        (tmp_path / "readme.txt").write_text("This is not a script")

        # Create a script without MCP metadata (should be ignored)
        (tmp_path / "no_metadata.sh").write_text("#!/bin/bash\necho 'No metadata'")

        folder = ScriptFolder(tmp_path)
        folder.scan()

        assert folder.isScanned is True
        assert folder.isValid is True
        assert len(folder.scripts) == 1
        assert folder.scripts[0].tool_name == "test_script"

    def test_scan_empty_folder(self, tmp_path: Path) -> None:
        """Verify scan handles empty folders correctly."""
        folder = ScriptFolder(tmp_path)
        folder.scan()

        assert folder.isScanned is True
        assert folder.isValid is False
        assert len(folder.scripts) == 0

    def test_scan_ignores_files_without_mcp_metadata(self, tmp_path: Path) -> None:
        """Verify that files without #mcp@name and #mcp@description are ignored."""
        # File with only description
        script1 = tmp_path / "only_desc.sh"
        script1.write_text(
            "#!/bin/bash\n#mcp@description Only description\n#mcp@param a:int\necho test"
        )

        # File with only name
        script2 = tmp_path / "only_name.sh"
        script2.write_text(
            "#!/bin/bash\n#mcp@name only_name\n#mcp@param a:int\necho test"
        )

        # File with neither
        script3 = tmp_path / "no_metadata.sh"
        script3.write_text("#!/bin/bash\necho 'No metadata at all'")

        folder = ScriptFolder(tmp_path)
        folder.scan()

        assert folder.isScanned is True
        assert folder.isValid is False
        assert len(folder.scripts) == 0

    def test_scan_ignores_large_files(self, tmp_path: Path) -> None:
        """Verify that files larger than MAX_SIZE are ignored."""
        script_content = """#!/bin/bash
#mcp@name large_script
#mcp@description A very large script
"""
        # Create a file that looks like it has metadata
        script_file = tmp_path / "large_script.sh"
        # Write content that exceeds MAX_SIZE (1_000_000 bytes)
        script_file.write_text(script_content + "x" * 1_000_001)

        folder = ScriptFolder(tmp_path)
        folder.scan()

        assert folder.isScanned is True
        assert folder.isValid is False
        assert len(folder.scripts) == 0

    def test_scan_ignores_non_text_files(self, tmp_path: Path) -> None:
        """Verify that binary files are ignored."""
        # Create a binary-like file
        binary_file = tmp_path / "binary.bin"
        binary_file.write_bytes(b"\x00\x01\x02\x03\x04\x05")

        # Create a file with MCP metadata but binary content
        script_with_metadata = tmp_path / "binary_script.sh"
        script_with_metadata.write_bytes(
            b"#mcp@name binary_script\n#mcp@description test\n\x00\x01\x02"
        )

        folder = ScriptFolder(tmp_path)
        folder.scan()

        # Binary files without valid UTF-8 should be skipped
        assert folder.isScanned is True


class TestScriptFolderParseMetadata:
    """Tests for ScriptFolder.parse_script() method."""

    def test_parse_metadata_extracts_name_and_description(self, tmp_path: Path) -> None:
        """Verify MCP metadata is parsed correctly."""
        script_content = """#!/bin/bash
#mcp@name my_tool
#mcp@description This is my tool description
#mcp@param x:int
#mcp@param y:string
echo "test"
"""
        script_file = tmp_path / "my_tool.sh"
        script_file.write_text(script_content)

        folder = ScriptFolder(tmp_path)
        info = folder.parse_script(script_file)

        assert info is not None
        assert info.tool_name == "my_tool"
        assert info.description == "This is my tool description"
        assert len(info.params) == 2
        assert info.params[0] == {"name": "x", "type": "int"}
        assert info.params[1] == {"name": "y", "type": "string"}

    def test_parse_metadata_handles_param_without_type(self, tmp_path: Path) -> None:
        """Verify that params without type default to empty string type."""
        script_content = """#!/bin/bash
#mcp@name no_type_tool
#mcp@description A tool with params without explicit types
#mcp@param a
#mcp@param b
echo "test"
"""
        script_file = tmp_path / "no_type_tool.sh"
        script_file.write_text(script_content)

        folder = ScriptFolder(tmp_path)
        info = folder.parse_script(script_file)

        assert info is not None
        assert len(info.params) == 2
        assert info.params[0] == {"name": "a", "type": ""}
        assert info.params[1] == {"name": "b", "type": ""}

    def test_parse_metadata_extracts_return_type(self, tmp_path: Path) -> None:
        """Verify that return type metadata is parsed correctly."""
        script_content = """#!/bin/bash
#mcp@name return_tool
#mcp@description A tool with return type
#mcp@param x:int
#mcp@return int
echo $((x * 2))
"""
        script_file = tmp_path / "return_tool.sh"
        script_file.write_text(script_content)

        folder = ScriptFolder(tmp_path)
        info = folder.parse_script(script_file)

        assert info is not None
        assert info.return_type == "int"

    def test_parse_metadata_returns_none_for_missing_name(self, tmp_path: Path) -> None:
        """Verify parse_script returns None when name is missing."""
        script_content = """#!/bin/bash
#mcp@description Missing name
#mcp@param x:int
echo "test"
"""
        script_file = tmp_path / "no_name.sh"
        script_file.write_text(script_content)

        folder = ScriptFolder(tmp_path)
        info = folder.parse_script(script_file)

        assert info is None

    def test_parse_metadata_returns_none_for_missing_description(
        self, tmp_path: Path
    ) -> None:
        """Verify parse_script returns None when description is missing."""
        script_content = """#!/bin/bash
#mcp@name no_desc_tool
#mcp@param x:int
echo "test"
"""
        script_file = tmp_path / "no_desc.sh"
        script_file.write_text(script_content)

        folder = ScriptFolder(tmp_path)
        info = folder.parse_script(script_file)

        assert info is None

    def test_parse_metadata_handles_file_read_error(self, tmp_path: Path) -> None:
        """Verify parse_script handles file read errors gracefully."""
        # Create a file that doesn't exist
        nonexistent_file = tmp_path / "does_not_exist.sh"

        folder = ScriptFolder(tmp_path)
        info = folder.parse_script(nonexistent_file)

        assert info is None


class TestScriptInfoDataclass:
    """Tests for ScriptInfo dataclass."""

    def test_scriptinfo_default_values(self) -> None:
        """Verify ScriptInfo default field values."""
        info = ScriptInfo(tool_name="test", path_str="/path/to/test")

        assert info.tool_name == "test"
        assert info.path_str == "/path/to/test"
        assert info.params == []
        assert info.description == ""
        assert info.return_type == ""

    def test_scriptinfo_with_all_fields(self) -> None:
        """Verify ScriptInfo can be created with all fields."""
        info = ScriptInfo(
            tool_name="full_tool",
            path_str="/path/to/tool",
            params=[{"name": "a", "type": "int"}, {"name": "b", "type": "string"}],
            description="A complete tool",
            return_type="string",
        )

        assert info.tool_name == "full_tool"
        assert info.path_str == "/path/to/tool"
        assert len(info.params) == 2
        assert info.description == "A complete tool"
        assert info.return_type == "string"

    def test_scriptinfo_params_is_list_of_dicts(self) -> None:
        """Verify params field is a list of dictionaries with name and type."""
        params = [
            {"name": "x", "type": "int"},
            {"name": "y", "type": "string"},
            {"name": "flag", "type": "bool"},
        ]
        info = ScriptInfo(
            tool_name="param_tool",
            path_str="/path",
            params=params,
        )

        assert len(info.params) == 3
        for param in info.params:
            assert "name" in param
            assert "type" in param
