"""Script folder scanner for extracting MCP tool metadata from shell scripts."""

import logging
from pathlib import Path

from scriptproxymcp.datatypes import ScriptInfo

logger = logging.getLogger("MCPScriptProxy")


class ScriptFolder:
    """Scans a folder for shell scripts with #mcp@ metadata and extracts tool definitions."""

    def __str__(self):
        """Return a human-readable representation of the script folder."""
        return f"ScriptFolder: {self.name} ({self.path})"

    def __init__(self, path: Path | str):
        """Initialize the script folder scanner.

        Args:
            path: Path to the folder containing scripts.
        """
        self.isScanned = False
        self.isValid = False
        self.path = path if isinstance(path, Path) else Path(path)
        self.scripts: list[ScriptInfo] = []
        self.name = self.path.name

    def scan(self):
        """Scan the folder for valid scripts with #mcp@ metadata.

        Skips files larger than 1 MiB and files missing required metadata tags.
        """
        logger.info("\nStart scan")
        # Maximum size in bytes
        max_size = 1_000_000

        for item in self.path.iterdir():
            # 1. Check if file
            if not item.is_file():
                continue

            # 2. Check if not too long (Größenprüfung)
            if item.stat().st_size > max_size:
                continue

            # 3. Check if '#mcp@description' inside
            try:
                # To be on the safe side, we read the file in text mode
                content = item.read_text(encoding="utf-8")
                if "#mcp@description" not in content:
                    continue
            except (UnicodeDecodeError, PermissionError):
                # If it is not a text file or access is denied
                continue

            # 4. Check if '#mcp@name' inside
            if "#mcp@name" not in content:
                continue

            # 5. create script info
            tmp_info = self.parse_script(item)
            if tmp_info:
                self.scripts.append(tmp_info)
                logger.info(f"Valid file found: {item.name}")

        self.isScanned = True
        self.isValid = len(self.scripts) > 0

    def parse_script(self, file_path: Path) -> ScriptInfo | None:
        """Parse a script file and extract its metadata."""
        info = ScriptInfo(tool_name="", path_str=str(file_path), description="", params=[])

        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()
        except OSError as e:
            logger.error(f"Warning: Could not read {file_path}: {e}")
            return None

        for line in lines:
            line = line.strip()

            if not line.startswith("#mcp@"):
                continue

            tag_content = line[5:].strip()  # Remove '#mcp@'

            if tag_content.startswith("description"):
                info.description = tag_content[11:].strip()

            elif tag_content.startswith("name"):
                info.tool_name = tag_content[4:].strip()

            elif tag_content.startswith("param"):
                param_def = tag_content[5:].strip()  # Skip 'param'
                if ":" not in param_def:
                    param = {"name": param_def.strip(), "type": ""}
                else:
                    name, type_ = param_def.split(":", 1)
                    param = {"name": name.strip(), "type": type_.strip()}
                info.params.append(param)

            elif tag_content.startswith("return"):
                info.return_type = tag_content[6:].strip()
        # check valid
        valid_params = all(param["name"] != "" for param in info.params)
        if info.description == "" or info.tool_name == "" or not valid_params:
            logger.error(f"Warning: Script {file_path} is missing name or description")
            return None

        return info
