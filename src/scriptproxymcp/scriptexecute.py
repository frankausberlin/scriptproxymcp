"""Script execution functionality for Script Proxy MCP."""

import json
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Callable

from scriptproxymcp.datatypes import RiskInfo, ScriptInfo

logger = logging.getLogger("MCPScriptProxy")

# Regex patterns to detect sudo/pkexec commands in scripts
SUDO_PATTERNS = [
    r"\bsudo\b",
    r"\bpkexec\b",
]


def detect_sudo_commands(script_content: str) -> list[str]:
    """Detect all sudo/pkexec commands in a script.

    Args:
        script_content: The full script content as a string.

    Returns:
        List of unique sudo/pkexec commands found in the script.
    """
    commands = set()
    for line in script_content.splitlines():
        line = line.strip()
        if line.startswith("#"):
            continue
        for pattern in SUDO_PATTERNS:
            matches = re.findall(pattern, line)
            if matches:
                # Extract the full command (from sudo/pkexec to end of line)
                for match in re.finditer(r"\b(sudo|pkexec)\s+(.+)$", line):
                    commands.add(f"{match.group(1)} {match.group(2).strip()}")
    return list(commands)


def build_sampling_request(command: str, script_path: str) -> dict[str, Any]:
    """Build a sampling request for risk assessment.

    Args:
        command: The sudo command to assess.
        script_path: Path to the script containing the command.

    Returns:
        Dictionary with sampling request parameters.
    """
    prompt = (
        f"Command: {command}\n"
        f"Script: {script_path}\n\n"
        "Please analyze this command and respond ONLY with a JSON object:\n"
        '{"purpose": "What does this command do?", '
        '"risk": "low|medium|high", '
        '"description": "Brief description of the risk"}'
    )
    return {
        "messages": [
            {
                "role": "user",
                "content": {"type": "text", "text": prompt},
            }
        ],
        "maxTokens": 500,
    }


def parse_sampling_response(response: str) -> RiskInfo:
    """Parse the sampling response into RiskInfo.

    Args:
        response: The LLM response as a string.

    Returns:
        RiskInfo object with parsed data.
    """
    try:
        # Try to extract JSON from the response
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return RiskInfo(
                purpose=data.get("purpose", ""),
                risk=data.get("risk", "unknown"),
                description=data.get("description", ""),
            )
    except (json.JSONDecodeError, AttributeError):
        pass
    return RiskInfo()


def select_sudo_command(commands: list[str]) -> str | None:
    """Select the most relevant sudo/pkexec command from a list.

    Args:
        commands: Detected sudo/pkexec commands.

    Returns:
        The preferred command, favoring askpass-enabled sudo usage
        when present.
    """
    for command in commands:
        if re.search(r"\bsudo\s+-A\b", command):
            return command

    return commands[0] if commands else None


def _get_primary_sudo_command(script_path: Path) -> str | None:
    """Extract the preferred sudo/pkexec command from a script.

    Args:
        script_path: Path to the script file.

    Returns:
        The preferred detected sudo/pkexec command, if any.
    """
    try:
        script_content = script_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None

    sudo_commands = detect_sudo_commands(script_content)
    return select_sudo_command(sudo_commands)


def validate_params(info: ScriptInfo, **kwargs: Any) -> tuple[bool, str]:
    """Validate that all required parameters are provided and no extra ones."""
    param_names = [p["name"] for p in info.params]

    # Check for missing parameters
    missing = [name for name in param_names if name not in kwargs]
    if missing:
        return False, f"Missing required parameters: {', '.join(missing)}"

    # Check for extra parameters
    extra = [key for key in kwargs if key not in param_names]
    if extra:
        return False, f"Unknown parameters: {', '.join(extra)}"

    return True, ""


def execute_script(
    script_path: Path | str,
    args: list[str],
    script_cwd: Path | str,
    risk_info: RiskInfo | None = None,
) -> str:
    """Execute the script with the given arguments and return stdout.

    Args:
        script_path: Path to the script to execute.
        args: Arguments to pass to the script.
        script_cwd: Working directory for script execution.
        risk_info: Optional risk assessment info to pass to askpass.

    Returns:
        The script's stdout output.
    """
    script_path = Path(script_path)
    script_cwd = Path(script_cwd)

    # Prepare environment for sudo handling
    env = os.environ.copy()
    if "ubuntuadminmcp" in str(script_path):
        # Set SUDO_ASKPASS for admin scripts
        askpass_path = Path(__file__).parent / "askpass_gui.py"
        env["SUDO_ASKPASS"] = str(askpass_path)

        sudo_command = _get_primary_sudo_command(script_path)
        if sudo_command:
            env["SCRIPTPROXY_SUDO_COMMAND"] = sudo_command

        # Pass risk info to askpass_gui via environment variables
        if risk_info:
            env["SCRIPTPROXY_RISK"] = risk_info.risk
            env["SCRIPTPROXY_PURPOSE"] = risk_info.purpose
            env["SCRIPTPROXY_DESCRIPTION"] = risk_info.description

    result = subprocess.run(
        [str(script_path), *args],
        cwd=str(script_cwd),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    if result.returncode != 0:
        error_msg = result.stderr.strip()
        if not error_msg:
            error_msg = f"Script exited with code {result.returncode}"
        raise RuntimeError(f"Script execution failed: {error_msg}")
    return result.stdout.strip()


def create_tool_function(
    info: ScriptInfo,
    risk_info_provider: Callable[[], RiskInfo | None] | None = None,
):
    """
    Factory function to create a tool function for a script.

    Args:
        info: ScriptInfo object with script metadata

    Returns:
        A callable tool function with proper signature for FastMCP
    """
    param_names = [p["name"] for p in info.params]
    script_path = Path(info.path_str)
    script_cwd = script_path.parent

    # Create a function with explicit parameters matching the script
    # This allows FastMCP to infer the correct input schema
    tool_func = _create_dynamic_function(
        info.tool_name,
        param_names,
        script_path,
        script_cwd,
        risk_info_provider,
    )

    return tool_func


def _create_dynamic_function(
    tool_name: str,
    param_names: list[str],
    script_path: Path,
    script_cwd: Path,
    risk_info_provider: Callable[[], RiskInfo | None] | None = None,
):
    """
    Create a function with explicit parameters at runtime.

    This ensures FastMCP infers the correct input schema with
    named parameters instead of a generic **kwargs.
    """
    # Build the function signature
    sig_params = ", ".join(param_names)
    func_code = f"""
def {tool_name}({sig_params}):
    '''
    Tool function for {tool_name}
    '''
    # Build kwargs from parameters
    kwargs = {{}}
"""
    for name in param_names:
        func_code += f"    kwargs['{name}'] = {name}\n"

    func_code += """
    # Validate and execute
    param_names = [p['name'] for p in info.params]
    is_valid, error_msg = validate_params(info, **kwargs)
    if not is_valid:
        raise ValueError(error_msg)

    risk_info = resolve_risk_info() if resolve_risk_info is not None else None
    args = [str(kwargs[name]) for name in param_names]
    return execute_script(script_path, args, script_cwd, risk_info)
"""

    # Create the function in a local namespace
    local_namespace = {
        "validate_params": validate_params,
        "execute_script": execute_script,
        "os": os,
        "resolve_risk_info": risk_info_provider,
        "info": ScriptInfo(
            tool_name=tool_name,
            path_str=str(script_path),
            params=[{"name": n} for n in param_names],
        ),
        "script_path": script_path,
        "script_cwd": script_cwd,
    }
    exec(func_code, local_namespace)

    return local_namespace[tool_name]


def _build_input_schema(info: ScriptInfo) -> dict[str, Any]:
    """Build input schema for a tool based on its params."""
    param_names = [p["name"] for p in info.params]
    param_types = {p["name"]: p.get("type", "string") for p in info.params}

    properties = {}
    required = []

    for name in param_names:
        param_type = param_types.get(name, "string")
        # Map script types to JSON schema types
        json_type = _map_script_type_to_json_type(param_type)
        properties[name] = {
            "title": name.title(),
            "type": json_type,
        }
        required.append(name)

    return {
        "properties": properties,
        "required": required,
        "title": f"{info.tool_name.title()}Arguments",
        "type": "object",
    }


def _map_script_type_to_json_type(script_type: str) -> str:
    """Map script parameter types to JSON schema types."""
    type_mapping = {
        "int": "number",
        "integer": "number",
        "float": "number",
        "number": "number",
        "string": "string",
        "str": "string",
        "bool": "boolean",
        "boolean": "boolean",
    }
    return type_mapping.get(script_type.lower(), "string")
