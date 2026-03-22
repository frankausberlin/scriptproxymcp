#!/usr/bin/env python3
"""Test client for MCP Script Proxy server.

This script tests the MCP server by:
1. Initializing the server via STDIO
2. Listing available tools
3. Calling the 'add' tool with parameters
4. Verifying the result

Usage:
    uv run python test_mcp_client.py
"""

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Run the MCP client test."""
    # Start the MCP server
    # fmt: off
    server_path = Path(__file__).parent / "src" / "scriptproxymcp" / "server.py"
    # fmt: on
    process = subprocess.Popen(
        [sys.executable, str(server_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    print("Starting MCP server test...")
    print(f"Server path: {server_path}")

    try:
        # Initialize the server
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        }
        print("\n[1] Sending initialize request...")
        print(f"Request: {json.dumps(init_request)}")
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()

        # Read initialization response
        init_response_line = process.stdout.readline()
        if init_response_line:
            init_response = json.loads(init_response_line)
            print(f"Response: {json.dumps(init_response)}")
            if "error" in init_response:
                print(f"ERROR: Initialize failed: {init_response['error']}")
                return 1
            print("Initialize: OK")
        else:
            print("ERROR: No response received for initialize")
            return 1

        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }
        process.stdin.write(json.dumps(initialized_notification) + "\n")
        process.stdin.flush()

        # List tools
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }
        print("\n[2] Sending tools/list request...")
        print(f"Request: {json.dumps(list_tools_request)}")
        process.stdin.write(json.dumps(list_tools_request) + "\n")
        process.stdin.flush()

        list_response_line = process.stdout.readline()
        if list_response_line:
            list_response = json.loads(list_response_line)
            print(f"Response: {json.dumps(list_response, indent=2)}")
            if "error" in list_response:
                print(f"ERROR: List tools failed: {list_response['error']}")
                return 1

            tools = list_response.get("result", {}).get("tools", [])
            print(f"\nFound {len(tools)} tools:")
            for tool in tools:
                desc = tool.get("description", "No description")
                print(f"  - {tool['name']}: {desc}")
            print("List tools: OK")
        else:
            print("ERROR: No response received for tools/list")
            return 1

        # Call the 'add' tool
        add_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "add",
                "arguments": {"a": 5, "b": 3},
            },
        }
        print("\n[3] Calling 'add' tool with a=5, b=3...")
        print(f"Request: {json.dumps(add_request)}")
        process.stdin.write(json.dumps(add_request) + "\n")
        process.stdin.flush()

        add_response_line = process.stdout.readline()
        if add_response_line:
            add_response = json.loads(add_response_line)
            print(f"Response: {json.dumps(add_response, indent=2)}")

            if "error" in add_response:
                print(f"ERROR: Call tool failed: {add_response['error']}")
                # Check stderr for debug output
                stderr_output = process.stderr.read()
                if stderr_output:
                    print(f"\nServer stderr:\n{stderr_output}")
                return 1

            # Extract result
            result = add_response.get("result", {})
            if "content" in result:
                for content in result["content"]:
                    if content.get("type") == "text":
                        output = content["text"]
                        print(f"\nTool output: {output}")

                        # Verify result
                        expected = "8"
                        if output == expected:
                            # fmt: off
                            print(f"\nSUCCESS: Got expected result '{expected}'")
                            # fmt: on
                        else:
                            # fmt: off
                            err = f"FAILURE: Expected '{expected}', got '{output}'"
                            print(f"\n{err}")
                            # fmt: on
                            return 1
            print("Call tool: OK")
        else:
            print("ERROR: No response received for tools/call")
            stderr_output = process.stderr.read()
            if stderr_output:
                print(f"\nServer stderr:\n{stderr_output}")
            return 1

        print("\n" + "=" * 50)
        print("All tests passed!")
        print("=" * 50)
        return 0

    finally:
        process.stdin.close()
        process.stdout.close()
        process.stderr.close()
        process.wait()


if __name__ == "__main__":
    sys.exit(main())
