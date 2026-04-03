"""Type definitions for MCP Script Proxy."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ScriptInfo:
    """Metadata extracted from a script file."""

    tool_name: str
    path_str: str
    params: list[dict[str, str]] = field(default_factory=list)
    description: str = ""
    return_type: str = ""


@dataclass
class SkillInfo:
    """Metadata extracted from a skill folder containing SKILL.md."""

    name: str
    path: Path
    description: str = ""
    files: list[str] = field(default_factory=list)
    scripts: list[ScriptInfo] = field(default_factory=list)


@dataclass
class PromptInfo:
    """Metadata extracted from a .prompt file."""

    name: str
    description: str = ""
    template: str = ""


@dataclass
class ServerInfo:
    """Metadata extracted from the server folder's mcpproxy.md file."""

    name: str
    description: str = ""
    folder: Path | None = None


@dataclass
class RiskInfo:
    """Risk assessment information from sampling analysis."""

    purpose: str = ""
    risk: str = "unknown"  # low, medium, high, unknown
    description: str = ""
