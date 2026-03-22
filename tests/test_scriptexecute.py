"""Unit tests for the script execution functionality."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scriptproxymcp.datatypes import ScriptInfo
from scriptproxymcp.scriptexecute import (
    _build_input_schema,
    _create_dynamic_function,
    _map_script_type_to_json_type,
    create_tool_function,
    execute_script,
    validate_params,
)


class TestValidateParams:
    """Tests for validate_params function."""

    def test_validate_params_returns_true_for_valid_params(self) -> None:
        """Verify validate_params returns True when all params are provided."""
        info = ScriptInfo(
            tool_name="test",
            path_str="/path",
            params=[{"name": "a", "type": "int"}, {"name": "b", "type": "string"}],
        )
        is_valid, error_msg = validate_params(info, a=1, b="hello")

        assert is_valid is True
        assert error_msg == ""

    def test_validate_params_returns_false_for_missing_params(self) -> None:
        """Verify validate_params returns False when required params are missing."""
        info = ScriptInfo(
            tool_name="test",
            path_str="/path",
            params=[{"name": "a", "type": "int"}, {"name": "b", "type": "string"}],
        )
        is_valid, error_msg = validate_params(info, a=1)

        assert is_valid is False
        assert "Missing required parameters: b" in error_msg

    def test_validate_params_returns_false_for_extra_params(self) -> None:
        """Verify validate_params returns False when extra params are provided."""
        info = ScriptInfo(
            tool_name="test",
            path_str="/path",
            params=[{"name": "a", "type": "int"}],
        )
        is_valid, error_msg = validate_params(info, a=1, extra_param="not_allowed")

        assert is_valid is False
        assert "Unknown parameters: extra_param" in error_msg

    def test_validate_params_with_empty_params(self) -> None:
        """Verify validate_params returns True when script has no params."""
        info = ScriptInfo(
            tool_name="no_params",
            path_str="/path",
            params=[],
        )
        is_valid, error_msg = validate_params(info)

        assert is_valid is True
        assert error_msg == ""


class TestExecuteScript:
    """Tests for execute_script function."""

    @patch("scriptproxymcp.scriptexecute.subprocess.run")
    def test_execute_script_success(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Verify execute_script returns stdout on successful execution."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "42"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        script_path = tmp_path / "test_script.sh"
        script_path.write_text("#!/bin/bash\necho 42")

        result = execute_script(script_path, ["arg1"], tmp_path)

        assert result == "42"
        mock_run.assert_called_once()

    @patch("scriptproxymcp.scriptexecute.subprocess.run")
    def test_execute_script_error(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Verify execute_script raises RuntimeError on non-zero exit code."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: something went wrong"
        mock_run.return_value = mock_result

        script_path = tmp_path / "failing_script.sh"

        with pytest.raises(RuntimeError, match="Script execution failed"):
            execute_script(script_path, [], tmp_path)

    @patch("scriptproxymcp.scriptexecute.subprocess.run")
    def test_execute_script_error_without_stderr(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Verify execute_script includes exit code in error when stderr is empty."""
        mock_result = MagicMock()
        mock_result.returncode = 127
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        script_path = tmp_path / "not_found.sh"

        with pytest.raises(RuntimeError, match="Script exited with code 127"):
            execute_script(script_path, [], tmp_path)


class TestCreateToolFunction:
    """Tests for create_tool_function factory function."""

    def test_create_tool_function_generates_callable(self) -> None:
        """Verify create_tool_function returns a callable function."""
        info = ScriptInfo(
            tool_name="my_add_tool",
            path_str="/path/to/script.sh",
            params=[{"name": "x", "type": "int"}, {"name": "y", "type": "int"}],
            description="Adds two numbers",
        )
        tool_func = create_tool_function(info)

        assert callable(tool_func)

    def test_create_tool_function_extracts_parameter_names(self) -> None:
        """Verify the generated function has the correct parameter names in its signature."""
        info = ScriptInfo(
            tool_name="calculator",
            path_str="/path/to/script.sh",
            params=[
                {"name": "first_num", "type": "int"},
                {"name": "second_num", "type": "int"},
            ],
            description="Calculator tool",
        )
        tool_func = create_tool_function(info)

        # Check that the function has the expected parameters
        import inspect

        sig = inspect.signature(tool_func)
        param_names = list(sig.parameters.keys())

        assert "first_num" in param_names
        assert "second_num" in param_names


class TestCreateDynamicFunction:
    """Tests for _create_dynamic_function helper."""

    def test_create_dynamic_function_with_parameters(self, tmp_path: Path) -> None:
        """Verify dynamic function creation with explicit parameters."""
        script_path = tmp_path / "test.sh"
        script_path.write_text("#!/bin/bash\necho hello")

        func = _create_dynamic_function(
            tool_name="greeting_tool",
            param_names=["name", "greeting"],
            script_path=script_path,
            script_cwd=tmp_path,
        )

        assert callable(func)

        # Check function signature
        import inspect

        sig = inspect.signature(func)
        params = list(sig.parameters.keys())

        assert "name" in params
        assert "greeting" in params

    def test_create_dynamic_function_no_params(self, tmp_path: Path) -> None:
        """Verify dynamic function creation works with no parameters."""
        script_path = tmp_path / "test.sh"
        script_path.write_text("#!/bin/bash\necho hello")

        func = _create_dynamic_function(
            tool_name="hello_tool",
            param_names=[],
            script_path=script_path,
            script_cwd=tmp_path,
        )

        assert callable(func)

        import inspect

        sig = inspect.signature(func)
        params = list(sig.parameters.keys())

        assert len(params) == 0


class TestBuildInputSchema:
    """Tests for _build_input_schema helper."""

    def test_build_input_schema_with_params(self) -> None:
        """Verify input schema is built correctly with parameters."""
        info = ScriptInfo(
            tool_name="add",
            path_str="/path",
            params=[{"name": "a", "type": "int"}, {"name": "b", "type": "string"}],
        )
        schema = _build_input_schema(info)

        assert "properties" in schema
        assert "required" in schema
        assert "a" in schema["properties"]
        assert "b" in schema["properties"]
        assert schema["required"] == ["a", "b"]

    def test_build_input_schema_title(self) -> None:
        """Verify input schema has correct title."""
        info = ScriptInfo(
            tool_name="my_tool",
            path_str="/path",
            params=[{"name": "x", "type": "int"}],
        )
        schema = _build_input_schema(info)

        assert schema["title"] == "My_ToolArguments"


class TestMapScriptTypeToJsonType:
    """Tests for _map_script_type_to_json_type helper."""

    def test_map_int_to_number(self) -> None:
        """Verify 'int' maps to 'number'."""
        assert _map_script_type_to_json_type("int") == "number"
        assert _map_script_type_to_json_type("integer") == "number"

    def test_map_float_to_number(self) -> None:
        """Verify 'float' maps to 'number'."""
        assert _map_script_type_to_json_type("float") == "number"

    def test_map_string_to_string(self) -> None:
        """Verify 'string' and 'str' map to 'string'."""
        assert _map_script_type_to_json_type("string") == "string"
        assert _map_script_type_to_json_type("str") == "string"

    def test_map_bool_to_boolean(self) -> None:
        """Verify 'bool' and 'boolean' map to 'boolean'."""
        assert _map_script_type_to_json_type("bool") == "boolean"
        assert _map_script_type_to_json_type("boolean") == "boolean"

    def test_map_unknown_to_string(self) -> None:
        """Verify unknown types default to 'string'."""
        assert _map_script_type_to_json_type("unknown") == "string"
        assert _map_script_type_to_json_type("") == "string"
