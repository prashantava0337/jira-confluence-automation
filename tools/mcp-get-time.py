#!/usr/bin/env python3
"""Minimal MCP stdio server exposing the local time."""
from datetime import datetime
import json
import sys

PROTOCOL_VERSION = "2025-06-18"
TIME_TOOL = {
    "name": "get_time",
    "description": "Get the current local time, including its UTC offset.",
    "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
}


def handle(request):
    method = request.get("method")
    params = request.get("params") or {}

    if method == "initialize":
        return {
            "protocolVersion": params.get("protocolVersion", PROTOCOL_VERSION),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "gettime-mac", "version": "1.0.0"},
        }
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": [TIME_TOOL]}
    if method == "tools/call":
        if params.get("name") != "get_time":
            raise ValueError(f"Unknown tool: {params.get('name')}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": datetime.now().astimezone().isoformat(timespec="seconds"),
                }
            ]
        }
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
        if request_id is None:
            continue

        try:
            response = {"jsonrpc": "2.0", "id": request_id, "result": handle(request)}
        except LookupError as exc:
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": str(exc)},
            }
        except Exception as exc:
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32602, "message": str(exc)},
            }

        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
