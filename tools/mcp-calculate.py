#!/usr/bin/env python3
"""Minimal MCP stdio server exposing basic arithmetic."""
import json
import math
import operator
import sys

PROTOCOL_VERSION = "2025-06-18"
OPERATIONS = {
    "add": operator.add,
    "subtract": operator.sub,
    "multiply": operator.mul,
    "divide": operator.truediv,
}

CALCULATE_TOOL = {
    "name": "calculate",
    "description": "Perform a basic arithmetic operation on two finite numbers.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": list(OPERATIONS),
                "description": "Arithmetic operation to perform.",
            },
            "a": {"type": "number", "description": "First operand."},
            "b": {"type": "number", "description": "Second operand."},
        },
        "required": ["operation", "a", "b"],
        "additionalProperties": False,
    },
}


def calculate(arguments):
    operation = arguments.get("operation")
    a = arguments.get("a")
    b = arguments.get("b")

    if operation not in OPERATIONS:
        raise ValueError(f"Unsupported operation: {operation}")
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in (a, b)):
        raise ValueError("Operands must be numbers.")
    if not math.isfinite(a) or not math.isfinite(b):
        raise ValueError("Operands must be finite numbers.")
    if operation == "divide" and b == 0:
        raise ValueError("Cannot divide by zero.")

    result = OPERATIONS[operation](a, b)
    if not math.isfinite(result):
        raise ValueError("The result is outside the supported numeric range.")
    return result


def handle(request):
    method = request.get("method")
    params = request.get("params") or {}

    if method == "initialize":
        return {
            "protocolVersion": params.get("protocolVersion", PROTOCOL_VERSION),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "Calculate-mac", "version": "1.0.0"},
        }
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": [CALCULATE_TOOL]}
    if method == "tools/call":
        if params.get("name") != "calculate":
            raise ValueError(f"Unknown tool: {params.get('name')}")
        result = calculate(params.get("arguments") or {})
        return {"content": [{"type": "text", "text": str(result)}]}
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
