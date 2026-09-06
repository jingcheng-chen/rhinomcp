"""Narrow assembly-task gateway; no evaluator, execution, or file access."""

import json

from mcp.server.fastmcp import FastMCP
from rhinomcp.server import get_rhino_connection
from rhinomcp.validation import validate_command
from experiments.runner import ROOT
from experiments.visual_mcp import guard, record

mcp = FastMCP("RhinoMCP layer assembly")
COMMANDS = frozenset(
    {
        "create_layer",
        "create_object",
        "update_object_attributes",
        "get_object_attributes",
        "get_objects",
        "delete_object",
    }
)


@mcp.tool()
def describe_command(command: str) -> dict:
    """Read an allowed command schema. Available: create_layer, create_object,
    update_object_attributes, get_object_attributes, get_objects, delete_object.
    BOX is centered at origin; translation offsets it. Units are millimeters.
    Use full layer paths when names repeat. No shell, code, import or export.
    """
    guard()
    if command not in COMMANDS:
        raise ValueError("Command outside assembly scope")
    return {
        "schema": json.loads(
            (ROOT / "contracts/commands" / (command + ".json")).read_text()
        ),
        "common_definitions": json.loads(
            (ROOT / "contracts/common/definitions.json").read_text()
        ),
    }


@mcp.tool()
def assembly_command(command: str, params: dict) -> dict:
    """Call an allowed command after reading its schema. Failures are recorded."""
    guard()
    if command not in COMMANDS:
        raise ValueError("Command outside assembly scope")
    validate_command(command, params)
    try:
        result = get_rhino_connection().send_command(command, params)
    except Exception as exc:
        record({"command": command, "params": params, "error": str(exc)})
        raise
    record({"command": command, "params": params, "result": result})
    return result


if __name__ == "__main__":
    mcp.run()
