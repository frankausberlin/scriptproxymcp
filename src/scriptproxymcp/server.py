"""ScriptProxyMCP arithmetic server."""

import math
from typing import Optional

from fastmcp import FastMCP


mcp = FastMCP("ScriptProxyMCP")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers."""
    return a - b


@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b


@mcp.tool()
def divide(a: int, b: int) -> Optional[float]:
    """Divide two numbers."""
    if b == 0:
        return None
    return a / b


@mcp.resource("math/constant/{name}")
def get_constant(name: str) -> Optional[float]:
    """Get the value of a mathematical constant like 'pi' or 'e'."""
    constants = {
        "pi": math.pi,
        "e": math.e,
        "tau": math.tau,
    }
    return constants.get(name.lower())


if __name__ == "__main__":
    mcp.run()
