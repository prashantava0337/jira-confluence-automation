#!/usr/bin/env python3
"""Minimal MCP server (stdio transport) exposing a single `echo` tool."""
import json
import sys

PROTOCOL_VERSION = "2025-06-18"

ECHO_TOOL = {
    "name": "echo",
    "description": "Echo back the given message.",
    "inputSchema": {
        "type": "object",
        "properties": {"message": {"type": "string", "description": "Text to echo."}},
        "required": ["message"],
    },
}


def handle(request):
    method = request.get("method")
    params = request.get("params") or {}

    if method == "initialize":
        return {
            "protocolVersion": params.get("protocolVersion", PROTOCOL_VERSION),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "echo-Mac", "version": "1.0.0"},
        }
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": [ECHO_TOOL]}
    if method == "tools/call":
        if params.get("name") != "echo":
            raise ValueError(f"Unknown tool: {params.get('name')}")
        message = (params.get("arguments") or {}).get("message", "")
        return {"content": [{"type": "text", "text": str(message)}]}
    raise LookupError(f"Method not found: {method}")


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue

        request_id = request.get("id")
        if request_id is None:  # notification, no response expected
            continue

        try:
            response = {"jsonrpc": "2.0", "id": request_id, "result": handle(request)}
        except LookupError as exc:
            response = {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": str(exc)}}
        except Exception as exc:
            response = {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": str(exc)}}

        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
