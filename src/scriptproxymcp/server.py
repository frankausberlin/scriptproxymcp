"""MCP Script Proxy Server.

This module provides an MCP server that exposes bash scripts as tools,
supports skills in subfolders, and provides prompts from .prompt files.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from mcp.server.fastmcp import FastMCP

from scriptproxymcp.datatypes import (
    PromptInfo,
    RiskInfo,
    ScriptInfo,
    ServerInfo,
    SkillInfo,
)
from scriptproxymcp.scriptexecute import (
    create_tool_function,
    detect_sudo_commands,
    select_sudo_command,
)

if TYPE_CHECKING:
    pass

# Basic configuration (once in the script)
logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s - %(name)s [%(module)s.%(funcName)s:%(lineno)d] - "
        "%(levelname)s - %(message)s"
    ),
)

logger = logging.getLogger("MCPScriptProxy")

# Default folder - use Path relative to this module, not CWD
_DEFAULT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_SERVER_FOLDER = str(_DEFAULT_ROOT / "demo" / "arithmeticmcp")
# Mandatory server config file
MCP_PROXY_CONFIG = "mcpproxy.md"


class MCPScriptProxy:
    """MCP server that exposes bash scripts as MCP tools.

    Architecture:
    - Folder name = Server name
    - mcpproxy.md (required) = Server description
    - *.sh files (recursive) = Tools (if they have #mcp@ metadata)
    - Subfolders with SKILL.md = Skills (as resources)
    - *.prompt files = Prompts
    """

    @staticmethod
    def get_server_folder() -> str:
        """Get the server folder from CLI args or environment variable.

        Priority:
        1. CLI positional argument (first argument)
        2. CLI --server-folder argument
        3. SERVER_FOLDER environment variable
        4. Default value

        Returns:
            Path to the server folder
        """
        parser = argparse.ArgumentParser(
            description="MCP server that exposes bash scripts as tools",
            add_help=False,
        )
        parser.add_argument(
            "server_folder",
            nargs="?",
            default=None,
            help="Path to the folder containing the MCP server",
        )
        parser.add_argument(
            "--server-folder",
            dest="server_folder_arg",
            default=None,
            help="Path to the folder containing the MCP server",
        )

        # Parse known args to avoid interfering with FastMCP's arg parsing
        known, _ = parser.parse_known_args()

        # Determine server folder with priority
        folder = (
            known.server_folder
            or known.server_folder_arg
            or os.environ.get("SERVER_FOLDER")
            or DEFAULT_SERVER_FOLDER
        )

        return folder

    def __init__(
        self,
        server_folder: str | None = None,
    ) -> None:
        self.mcp: FastMCP | None = None
        folder_path = server_folder or MCPScriptProxy.get_server_folder()
        folder_path_obj = Path(folder_path)

        # If path is relative and starts with ./ or ../, resolve relative
        # to script directory
        if not folder_path_obj.is_absolute() and (
            folder_path.startswith("./") or folder_path.startswith("../")
        ):
            script_dir = Path(__file__).parent.parent.parent
            folder_path_obj = script_dir / folder_path
            msg = f"Resolved relative path '{folder_path}' to '{folder_path_obj}'"
            logger.info(msg)

        # Convert to absolute path for reliable subprocess execution
        self.folder_path = folder_path_obj.resolve()

        # Initialize collections
        self.server_info: ServerInfo | None = None
        self.scripts: list[ScriptInfo] = []
        self.skills: list[SkillInfo] = []
        self.prompts: list[PromptInfo] = []
        # Sampling support flag
        self.sampling_enabled = True

    def scan(self) -> bool:
        """Scan the folder for server configuration.

        Returns:
            True if the server folder is valid, False otherwise
        """
        logger.info(f"Scanning server folder: {self.folder_path}")

        # 1. Check if folder exists
        logger.info(f"Checking if folder exists: {self.folder_path.exists()}")
        if not self.folder_path.exists():
            logger.error(f"Server folder does not exist: {self.folder_path}")
            return False

        is_dir = self.folder_path.is_dir()
        logger.info(f"Checking if folder is directory: {is_dir}")
        if not self.folder_path.is_dir():
            logger.error(f"Server path is not a directory: {self.folder_path}")
            return False

        # 2. Read mcpproxy.md (required)
        logger.info("Reading mcpproxy.md...")
        self.server_info = self._read_mcpproxy_md()
        if not self.server_info:
            logger.error(
                f"mcpproxy.md not found in {self.folder_path}. "
                "This file is required for server configuration."
            )
            return False

        logger.info(f"Server name: {self.server_info.name}")

        # 3. Scan for scripts (recursive)
        logger.info("Scanning for scripts...")
        self.scripts = self._scan_scripts()
        logger.info(f"Found {len(self.scripts)} script(s)")

        # 4. Scan for skills (subfolders with SKILL.md)
        logger.info("Scanning for skills...")
        self.skills = self._scan_skills()
        logger.info(f"Found {len(self.skills)} skill(s)")

        # 5. Scan for prompts (*.prompt files)
        logger.info("Scanning for prompts...")
        self.prompts = self._scan_prompts()
        logger.info(f"Found {len(self.prompts)} prompt(s)")

        return True

    def _read_mcpproxy_md(self) -> ServerInfo | None:
        """Read the mcpproxy.md file for server configuration.

        Returns:
            ServerInfo object, or None if file not found
        """
        config_path = self.folder_path / MCP_PROXY_CONFIG
        if not config_path.exists():
            return None

        try:
            content = config_path.read_text(encoding="utf-8")
            lines = content.splitlines()

            # Server name comes from folder name
            server_name = self.folder_path.name

            # Rest of content is the description
            desc_lines = [line.strip() for line in lines if line.strip()]
            # Skip first line (could be a heading) and join the rest
            if len(desc_lines) > 1:
                description = " ".join(desc_lines[1:])
            else:
                description = desc_lines[0] if desc_lines else ""

            return ServerInfo(
                name=server_name,
                description=description,
                folder=self.folder_path,
            )

        except (UnicodeDecodeError, OSError) as e:
            logger.error(f"Error reading {config_path}: {e}")
            return None

    def _scan_scripts(self) -> list[ScriptInfo]:
        """Scan folder recursively for .sh files with #mcp@ metadata.

        Returns:
            List of ScriptInfo objects
        """
        scripts: list[ScriptInfo] = []

        for sh_file in self.folder_path.rglob("*.sh"):
            script_info = self._parse_script(sh_file)
            if script_info:
                scripts.append(script_info)

        return scripts

    def _parse_script(self, script_path: Path) -> ScriptInfo | None:
        """Parse a script file for #mcp@ metadata.

        Args:
            script_path: Path to the script file

        Returns:
            ScriptInfo object, or None if invalid
        """
        try:
            content = script_path.read_text(encoding="utf-8")
            lines = content.splitlines()

            tool_name = ""
            description = ""
            params: list[dict[str, str]] = []

            for line in lines:
                stripped = line.strip()
                if stripped.startswith("#mcp@name:"):
                    tool_name = stripped[10:].strip()
                elif stripped.startswith("#mcp@description:"):
                    description = stripped[17:].strip()
                elif stripped.startswith("#mcp@param:"):
                    # Format: #mcp@param name:type or #mcp@param name
                    param_part = stripped[11:].strip()
                    if ":" in param_part:
                        name, param_type = param_part.split(":", 1)
                        params.append(
                            {
                                "name": name.strip(),
                                "type": param_type.strip(),
                            }
                        )
                    else:
                        params.append({"name": param_part, "type": ""})

            # Valid script must have name and description
            if not tool_name or not description:
                return None

            return ScriptInfo(
                tool_name=tool_name,
                path_str=str(script_path),
                description=description,
                params=params,
            )

        except (UnicodeDecodeError, OSError) as e:
            logger.warning(f"Error reading script {script_path}: {e}")
            return None

    def _scan_skills(self) -> list[SkillInfo]:
        """Scan subfolders for skills (folders containing SKILL.md).

        Returns:
            List of SkillInfo objects
        """
        skills: list[SkillInfo] = []

        for item in self.folder_path.iterdir():
            if not item.is_dir():
                continue

            skill_md = item / "SKILL.md"
            if skill_md.exists():
                skill_info = self._parse_skill(item)
                if skill_info:
                    skills.append(skill_info)

        return skills

    def _parse_skill(self, skill_path: Path) -> SkillInfo | None:
        """Parse a skill folder for SKILL.md metadata.

        Args:
            skill_path: Path to the skill folder

        Returns:
            SkillInfo object, or None if invalid
        """
        skill_md = skill_path / "SKILL.md"
        name = skill_path.name
        description = ""

        try:
            content = skill_md.read_text(encoding="utf-8")
            lines = content.splitlines()
            in_frontmatter = False
            frontmatter_lines: list[str] = []
            content_lines: list[str] = []

            for line in lines:
                stripped = line.strip()
                if stripped.startswith("---"):
                    in_frontmatter = not in_frontmatter
                    continue
                if in_frontmatter:
                    frontmatter_lines.append(stripped)
                elif stripped:
                    content_lines.append(stripped)

            # Extract name and description from frontmatter
            for fm_line in frontmatter_lines:
                if fm_line.startswith("name:"):
                    name = fm_line[5:].strip()
                elif fm_line.startswith("description:"):
                    description = fm_line[12:].strip()

            # Fallback description from content
            if not description and content_lines:
                first_line = content_lines[0]
                if first_line.startswith("#"):
                    first_line = first_line.lstrip("# ").strip()
                description = first_line
                if len(description) > 200:
                    description = description[:200] + "..."

        except (UnicodeDecodeError, OSError) as e:
            logger.warning(f"Error reading skill {skill_md}: {e}")
            return None

        # Collect skill scripts from scripts/ subfolder
        skill_scripts: list[ScriptInfo] = []
        scripts_folder = skill_path / "scripts"
        if scripts_folder.exists() and scripts_folder.is_dir():
            for sh_file in scripts_folder.rglob("*.sh"):
                script_info = self._parse_script(sh_file)
                if script_info:
                    skill_scripts.append(script_info)

        # Collect all files in skill folder
        files: list[str] = []
        for item in skill_path.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(skill_path)
                files.append(str(rel_path))

        return SkillInfo(
            name=name,
            path=skill_path,
            description=description,
            files=sorted(files),
            scripts=skill_scripts,
        )

    def _scan_prompts(self) -> list[PromptInfo]:
        """Scan folder for .prompt files.

        Returns:
            List of PromptInfo objects
        """
        prompts: list[PromptInfo] = []

        for prompt_file in self.folder_path.rglob("*.prompt"):
            prompt_info = self._parse_prompt(prompt_file)
            if prompt_info:
                prompts.append(prompt_info)

        return prompts

    def _parse_prompt(self, prompt_path: Path) -> PromptInfo | None:
        """Parse a .prompt file.

        Args:
            prompt_path: Path to the prompt file

        Returns:
            PromptInfo object, or None if invalid
        """
        try:
            content = prompt_path.read_text(encoding="utf-8")

            # Try to parse as JSON
            try:
                data = json.loads(content)
                name = data.get("name", prompt_path.stem)
                description = data.get("description", "")
                template = json.dumps(data, indent=2)
            except json.JSONDecodeError:
                # Fallback: use filename as name, content as template
                name = prompt_path.stem
                description = ""
                template = content

            return PromptInfo(
                name=name,
                description=description,
                template=template,
            )

        except (UnicodeDecodeError, OSError) as e:
            logger.warning(f"Error reading prompt {prompt_path}: {e}")
            return None

    def run(self) -> None:
        """Run the MCP server."""
        if not self.server_info:
            logger.error("Server not configured. Call scan() first.")
            return

        logger.info(f"Building MCP server '{self.server_info.name}'...")
        self.mcp = FastMCP(self.server_info.name)

        # Register tools from scripts
        self._register_tools()

        # Register skills as resources
        self._register_skill_resources()

        # Register prompts
        self._register_prompts()

        # Register skill-generated prompts
        self._register_skill_prompts()

    def _register_tools(self) -> None:
        """Register script tools with the MCP server."""
        mcp = self.mcp
        assert mcp is not None
        for script in self.scripts:
            tool_func = create_tool_function(
                script,
                self._build_risk_info_provider(script),
            )
            mcp.add_tool(
                tool_func,
                name=script.tool_name,
                description=script.description,
            )
            logger.info(f"Registered tool: {script.tool_name}")

    def _build_risk_info_provider(
        self,
        script: ScriptInfo,
    ) -> Callable[[], RiskInfo | None] | None:
        """Build an optional risk info provider for a script.

        Args:
            script: The ScriptInfo object for the script.

        Returns:
            A zero-argument callable that returns RiskInfo, or None if the
            script does not require elevated privileges.
        """
        script_path = Path(script.path_str)

        # Read script content to detect sudo commands
        try:
            script_content = script_path.read_text(encoding="utf-8")
            sudo_commands = detect_sudo_commands(script_content)
        except (UnicodeDecodeError, OSError):
            sudo_commands = []

        if not sudo_commands:
            return None

        command = select_sudo_command(sudo_commands)
        if command is None:
            return None

        def resolve_risk_info() -> RiskInfo | None:
            """Resolve risk info lazily when the tool is executed."""
            if not self.sampling_enabled:
                return None

            return self._perform_sampling(command, str(script_path))

        return resolve_risk_info

    def _perform_sampling(self, command: str, script_path: str) -> RiskInfo:
        """Perform sampling to get risk assessment.

        Args:
            command: The sudo command to assess.
            script_path: Path to the script.

        Returns:
            RiskInfo with the assessment result.
        """
        # Note: FastMCP doesn't support sampling natively.
        # Sampling requires migration to low-level Server API.
        # For now, always use fallback risk info.
        logger.debug("Sampling not supported by FastMCP, using fallback risk info")
        return self._get_fallback_risk_info(command)

    def _get_fallback_risk_info(self, command: str) -> RiskInfo:
        """Get fallback risk info based on regex command analysis.

        Args:
            command: The sudo command to analyze.

        Returns:
            RiskInfo with basic assessment.
        """
        command_lower = command.lower()

        # Low risk commands - read-only operations
        low_risk_patterns = [
            (
                r"\b(journalctl|systemctl\s+status|cat\s+/var/log|dmesg|"
                r"uptime|free|df|top|ps|ls|cat|less|more|head|tail|grep|"
                r"find|which|whereis|man|info)\b"
            ),
        ]
        for pattern in low_risk_patterns:
            if re.search(pattern, command_lower):
                return RiskInfo(
                    purpose="Read system information or logs",
                    risk="low",
                    description="This command reads system information "
                    "without modifying anything.",
                )

        # Medium risk commands - service management, non-destructive changes
        medium_risk_patterns = [
            (
                r"\b(systemctl\s+(restart|reload|stop|start|enable|disable|"
                r"mask|unmask))\b"
            ),
            r"\b(service\s+\w+\s+(restart|reload|stop|start))\b",
            r"\b(chmod|chown|chgrp)\b",
            r"\b(mkdir|mv|cp|ln)\b",
            r"\b(useradd|usermod|groupadd|groupmod)\b",
        ]
        for pattern in medium_risk_patterns:
            if re.search(pattern, command_lower):
                return RiskInfo(
                    purpose="Manage system services or configuration",
                    risk="medium",
                    description="This command may affect running services "
                    "or modify system configuration.",
                )

        # High risk commands - destructive operations
        high_risk_patterns = [
            r"\b(rm\s+(-rf?|--recursive))\b",
            r"\b(mkfs|fdisk|parted|dd|shred)\b",
            r"\b(chmod\s+777)\b",
            r"\b(chown\s+root)\b",
            r"\b(userdel|groupdel)\b",
            r"\b(format|mkswap|swapon)\b",
        ]
        for pattern in high_risk_patterns:
            if re.search(pattern, command_lower):
                return RiskInfo(
                    purpose="Potentially destructive operation",
                    risk="high",
                    description="WARNING: This command may cause data loss "
                    "or system instability!",
                )

        # Default
        return RiskInfo(
            purpose=f"Execute: {command}",
            risk="medium",
            description="This command requires elevated privileges.",
        )

    def _register_skill_resources(self) -> None:
        """Register skill resources with the MCP server."""
        mcp = self.mcp
        assert mcp is not None

        def register_skill(s: SkillInfo) -> None:
            # Resource for the skill's SKILL.md
            @mcp.resource(f"skills://{s.name}/SKILL.md")
            def get_skill_md() -> str:
                """Returns the content of the SKILL.md file."""
                skill_md_path = s.path / "SKILL.md"
                try:
                    return skill_md_path.read_text(encoding="utf-8")
                except (UnicodeDecodeError, OSError) as e:
                    return f"Error: Could not read SKILL.md: {e}"

            # Resource for skill files
            @mcp.resource(f"skills://{s.name}/{{file_path}}")
            def get_skill_file(file_path: str) -> str:
                """Returns content of a file in the skill folder."""
                full_path = s.path / file_path
                if not full_path.exists():
                    return f"Error: File '{file_path}' not found"
                try:
                    return full_path.read_text(encoding="utf-8")
                except (UnicodeDecodeError, OSError) as e:
                    return f"Error: Could not read file: {e}"

            logger.info(f"Registered resources for skill: {s.name}")

            # Register skill scripts as tools
            for script in s.scripts:
                tool_func = create_tool_function(
                    script,
                    self._build_risk_info_provider(script),
                )
                tool_name = f"{s.name}_{script.tool_name}"
                mcp.add_tool(
                    tool_func,
                    name=tool_name,
                    description=f"[{s.name}] {script.description}",
                )
                logger.info(f"Registered skill tool: {tool_name}")

        for skill in self.skills:
            register_skill(skill)

    def _register_prompts(self) -> None:
        """Register prompts from .prompt files."""
        mcp = self.mcp
        assert mcp is not None

        def register_prompt(p: PromptInfo) -> None:
            @mcp.prompt(name=p.name, description=p.description)
            def prompt_func() -> str:
                return p.template

        for prompt in self.prompts:
            desc_preview = prompt.description[:50]
            logger.info(f"Prompt '{prompt.name}': {desc_preview}...")
            register_prompt(prompt)

    def _register_skill_prompts(self) -> None:
        """Register prompts generated from skills."""
        mcp = self.mcp
        assert mcp is not None

        def register_skill_prompt(s: SkillInfo, text: str) -> None:
            @mcp.prompt(
                name=f"{s.name}_skill",
                description=f"Use the {s.name} skill",
            )
            def prompt_func() -> str:
                return text

        for skill in self.skills:
            # Generate prompt text based on skill metadata
            prompt_text = self._generate_skill_prompt(skill)
            prompt_preview = prompt_text[:50]
            msg = f"Generated prompt for skill '{skill.name}': {prompt_preview}..."
            logger.info(msg)
            register_skill_prompt(skill, prompt_text)

    def _generate_skill_prompt(self, skill: SkillInfo) -> str:
        """Generate a prompt description for a skill.

        Args:
            skill: The SkillInfo object

        Returns:
            A string describing when and how to use the skill
        """
        parts = [f"Use the '{skill.name}' skill when: {skill.description}"]

        if skill.scripts:
            script_names = [s.tool_name for s in skill.scripts]
            parts.append(f"Available tools: {', '.join(script_names)}")

        if skill.files:
            parts.append(f"Available files: {', '.join(skill.files[:5])}")
            if len(skill.files) > 5:
                parts.append(f"... and {len(skill.files) - 5} more files")

        return " ".join(parts)


def main() -> None:
    """Entry point for the MCP server."""
    server_folder = MCPScriptProxy.get_server_folder()
    server = MCPScriptProxy(server_folder)

    if not server.scan():
        logger.error("Failed to scan server folder")
        return

    server.run()

    if server.mcp is None:
        raise RuntimeError("Failed to initialize MCP server")

    server.mcp.run()


if __name__ == "__main__":
    main()
