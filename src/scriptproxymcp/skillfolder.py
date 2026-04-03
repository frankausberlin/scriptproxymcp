"""Skill folder scanner for MCP Script Proxy."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from scriptproxymcp.datatypes import ScriptInfo, SkillInfo
from scriptproxymcp.scriptfolder import ScriptFolder

if TYPE_CHECKING:
    pass

logger = logging.getLogger("MCPScriptProxy")


class SkillFolder:
    """Scans a folder for SKILL.md to detect a Kilo Code skill.

    This class supports two use cases:
    1. If the folder itself contains SKILL.md, it's a single skill folder
    2. If the folder contains subdirectories with SKILL.md, it scans for skills

    The mode is auto-detected based on whether the root folder has SKILL.md.
    """

    def __init__(self, path: Path | str) -> None:
        self.isScanned = False
        self.isValid = False
        self.path = path if isinstance(path, Path) else Path(path)
        self.skills: list[SkillInfo] = []
        self.name = self.path.name
        # Mode: True if this folder itself is a skill (has SKILL.md)
        self.is_single_skill = (self.path / "SKILL.md").exists()

    @property
    def folder_path(self) -> Path:
        """Alias for path to maintain compatibility."""
        return self.path

    def scan(self) -> None:
        """Scan the folder for skills.

        If the folder itself contains SKILL.md, it represents a single skill.
        Otherwise, it scans subdirectories for SKILL.md files.
        """
        logger.info("\nStart skill scan")

        if not self.path.exists():
            logger.error(f"Skill folder does not exist: {self.path}")
            self.isScanned = True
            self.isValid = False
            return

        if not self.path.is_dir():
            logger.error(f"Skill path is not a directory: {self.path}")
            self.isScanned = True
            self.isValid = False
            return

        if self.is_single_skill:
            # This folder IS a skill (has SKILL.md)
            self._scan_single_skill()
        else:
            # Scan subdirectories for skills
            self._scan_subfolders_for_skills()

        self.isScanned = True
        self.isValid = len(self.skills) > 0
        logger.info(f"Scan complete. Found {len(self.skills)} skills.")

    def _scan_single_skill(self) -> None:
        """Scan this folder as a single skill (it has SKILL.md)."""
        logger.info(f"Single skill detected: {self.path.name}")
        skill_info = self._parse_skill(self.path)
        if skill_info:
            self.skills.append(skill_info)
            logger.info(f"Valid skill found: {self.path.name}")

    def _scan_subfolders_for_skills(self) -> None:
        """Scan subdirectories for SKILL.md files."""
        for item in self.path.iterdir():
            if not item.is_dir():
                continue

            skill_md = item / "SKILL.md"
            if skill_md.exists() and skill_md.is_file():
                skill_info = self._parse_skill(item)
                if skill_info:
                    self.skills.append(skill_info)
                    logger.info(f"Valid skill found: {item.name}")

    def _parse_skill(self, skill_path: Path) -> SkillInfo | None:
        """Parse a skill folder and extract its metadata.

        Args:
            skill_path: Path to the skill folder (must have SKILL.md)

        Returns:
            SkillInfo object with metadata, or None if parsing fails
        """
        skill_md = skill_path / "SKILL.md"
        name = ""
        description = ""

        try:
            content = skill_md.read_text(encoding="utf-8")
            lines = content.splitlines()
            in_frontmatter = False
            frontmatter_lines: list[str] = []
            content_lines: list[str] = []

            for line in lines:
                stripped = line.strip()
                # Handle frontmatter markers
                if stripped.startswith("---"):
                    in_frontmatter = not in_frontmatter
                    continue
                # Collect frontmatter lines
                if in_frontmatter:
                    frontmatter_lines.append(stripped)
                    continue
                # Collect content lines after frontmatter
                if stripped:
                    content_lines.append(stripped)

            # Extract name and description from frontmatter
            for fm_line in frontmatter_lines:
                if fm_line.startswith("name:"):
                    name = fm_line[5:].strip()
                elif fm_line.startswith("description:"):
                    description = fm_line[12:].strip()

            # If no description in frontmatter, use first content line
            if not description and content_lines:
                first_line = content_lines[0]
                # Remove markdown heading prefix
                if first_line.startswith("#"):
                    first_line = first_line.lstrip("# ").strip()
                description = first_line
                if len(description) > 200:
                    description = description[:200] + "..."

            # Use folder name if no name in frontmatter
            if not name:
                name = skill_path.name

        except (UnicodeDecodeError, OSError, PermissionError) as e:
            logger.error(f"Warning: Could not read {skill_md}: {e}")
            return None

        files = self._collect_skill_files(skill_path)
        scripts = self._collect_skill_scripts(skill_path)

        return SkillInfo(
            name=name,
            path=skill_path,
            description=description,
            files=files,
            scripts=scripts,
        )

    def _collect_skill_files(self, skill_path: Path) -> list[str]:
        """Collect all file paths relative to the skill folder.

        Args:
            skill_path: Path to the skill folder

        Returns:
            List of relative file paths
        """
        files: list[str] = []
        for item in skill_path.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(skill_path)
                files.append(str(rel_path))
        return sorted(files)

    def _collect_skill_scripts(self, skill_path: Path) -> list[ScriptInfo]:
        """Collect scripts from the skill's scripts/ subfolder.

        Scans <skill_path>/scripts/ for .sh files containing #mcp@ metadata
        and returns them as ScriptInfo objects.

        Args:
            skill_path: Path to the skill folder

        Returns:
            List of ScriptInfo objects from the scripts/ subfolder
        """
        scripts_folder = skill_path / "scripts"
        if not scripts_folder.exists() or not scripts_folder.is_dir():
            return []

        script_folder = ScriptFolder(scripts_folder)
        script_folder.scan()

        if script_folder.isValid:
            n_found = len(script_folder.scripts)
            logger.info(f"Found {n_found} scripts in {skill_path.name}")
        return script_folder.scripts

    def get_skill(self, name: str) -> SkillInfo | None:
        """Get a skill by name.

        Args:
            name: Skill name to find

        Returns:
            SkillInfo if found, None otherwise
        """
        for skill in self.skills:
            if skill.name == name:
                return skill
        return None

    def get_skill_file(self, skill_name: str, file_path: str) -> Path | None:
        """Resolve a file path within a skill folder.

        Args:
            skill_name: Name of the skill
            file_path: Relative file path within the skill

        Returns:
            Full Path to the file if found, None otherwise
        """
        skill = self.get_skill(skill_name)
        if not skill:
            return None
        full_path = skill.path / file_path
        if full_path.exists() and full_path.is_file():
            return full_path
        return None
