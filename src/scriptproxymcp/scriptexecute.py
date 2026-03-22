"""Script execution functionality for Script Proxy MCP."""

import subprocess
from pathlib import Path
from typing import Any

from scriptproxymcp.datatypes import ScriptInfo


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
    script_path: Path | str, args: list[str], script_cwd: Path | str
) -> str:
    """Execute the script with the given arguments and return stdout."""
    script_path = Path(script_path)
    script_cwd = Path(script_cwd)

    result = subprocess.run(
        [str(script_path), *args],
        cwd=str(script_cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        error_msg = result.stderr.strip()
        if not error_msg:
            error_msg = f"Script exited with code {result.returncode}"
        raise RuntimeError(f"Script execution failed: {error_msg}")
    return result.stdout.strip()


def create_tool_function(info: ScriptInfo):
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
        info.tool_name, param_names, script_path, script_cwd
    )

    return tool_func


def _create_dynamic_function(
    tool_name: str,
    param_names: list[str],
    script_path: Path,
    script_cwd: Path,
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

    args = [str(kwargs[name]) for name in param_names]
    return execute_script(script_path, args, script_cwd)
"""

    # Create the function in a local namespace
    local_namespace = {
        "validate_params": validate_params,
        "execute_script": execute_script,
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
