"""Unit tests for the ScriptProxyMCP server tools and resource resolver."""

import math

from scriptproxymcp.server import add, divide, get_constant, mcp, multiply, subtract


def test_add_returns_sum() -> None:
    assert add(2, 3) == 5
    assert add(-4, 7) == 3


def test_subtract_returns_difference() -> None:
    assert subtract(10, 3) == 7
    assert subtract(-2, -5) == 3


def test_multiply_returns_product() -> None:
    assert multiply(6, 7) == 42
    assert multiply(-3, 4) == -12


def test_divide_returns_quotient() -> None:
    assert divide(8, 2) == 4
    assert divide(7, 2) == 3.5


def test_divide_by_zero_returns_none() -> None:
    assert divide(1, 0) is None


def test_get_constant_is_case_insensitive() -> None:
    assert get_constant("pi") == math.pi
    assert get_constant("PI") == math.pi
    assert get_constant("e") == math.e
    assert get_constant("Tau") == math.tau


def test_get_constant_returns_none_for_unknown_name() -> None:
    assert get_constant("unknown") is None


def test_mcp_application_is_initialized() -> None:
    assert mcp is not None
    assert mcp.name == "ScriptProxyMCP"
