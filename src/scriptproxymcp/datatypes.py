"""Type definitions for MCP Script Proxy."""

from dataclasses import dataclass, field


@dataclass
class ScriptInfo:
    """Metadata extracted from a script file."""

    tool_name: str
    path_str: str
    params: list[dict[str, str]] = field(default_factory=list)
    # param_names: list[str] = field(default_factory=list)
    description: str = ""
    return_type: str = ""
