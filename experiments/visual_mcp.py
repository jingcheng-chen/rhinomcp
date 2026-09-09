"""Bounded gateway for screenshot benchmarks; no execution or hidden-file tools."""

import base64
import json
import os
from pathlib import Path

from mcp.server.mcpserver import Image, MCPServer
from rhinomcp.server import get_rhino_connection
from rhinomcp.validation import validate_command
from experiments.bridge import assert_document
from experiments.rhino_trial import runtime, require_owned
from experiments.runner import ROOT, sha256

mcp = MCPServer("RhinoMCP visual benchmark")
COMMANDS = frozenset(
    {
        "create_object",
        "create_objects",
        "modify_object",
        "modify_objects",
        "delete_object",
        "extrude_curve",
        "loft",
        "sweep1",
        "pipe",
        "offset_curve",
        "boolean_difference",
        "boolean_union",
        "analyze_objects",
        "get_objects",
        "create_layer",
        "update_object_attributes",
    }
)
calls = 0


def guard():
    global calls
    calls += 1
    if calls > int(os.environ["EXPERIMENT_MAX_CALLS"]):
        raise RuntimeError("Tool budget exhausted")
    owner = {
        "pid": int(os.environ["EXPERIMENT_PID"]),
        "document": int(os.environ["EXPERIMENT_DOCUMENT"]),
    }
    require_owned(runtime(), owner)
    assert_document(owner["document"], os.environ["EXPERIMENT_MARKER"])


def record(value):
    with Path(os.environ["EXPERIMENT_TOOL_LOG"]).open("a") as output:
        output.write(json.dumps(value) + "\n")


@mcp.tool()
def describe_modeling_command(command: str) -> dict:
    """Read the exact existing RhinoMCP parameter schema before using a command.

    Available: create_object, create_objects, modify_object, modify_objects,
    delete_object, extrude_curve, loft, sweep1, pipe, offset_curve,
    boolean_difference, boolean_union, analyze_objects, get_objects,
    create_layer, update_object_attributes.
    BOX is centered on origin; rotation/scale use the world bounding-box center.
    CURVE points are control points, not necessarily interpolation points.
    Extrusion/sweep/loft leave their source curves; remove construction geometry.
    Units are millimeters. No arbitrary code, shell, import, or file operations.
    """
    guard()
    if command not in COMMANDS:
        raise ValueError("Command is outside the benchmark scope")
    return {
        "schema": json.loads(
            (ROOT / "contracts/commands" / f"{command}.json").read_text()
        ),
        "common_definitions": json.loads(
            (ROOT / "contracts/common/definitions.json").read_text()
        ),
    }


@mcp.tool()
def modeling_command(command: str, params: dict) -> dict:
    """Call an allowed existing modeling command using its exact parameter schema.

    Read describe_modeling_command first. Results and failures are recorded.
    There is no code execution or file import/export through this tool.
    """
    guard()
    if command not in COMMANDS:
        raise ValueError("Command is outside the benchmark scope")
    if os.environ.get("EXPERIMENT_READ_ONLY") == "1":
        raise RuntimeError("Review gateway cannot execute modeling commands")
    validate_command(command, params)
    try:
        result = get_rhino_connection().send_command(command, params)
    except Exception as error:
        record({"command": command, "params": params, "error": str(error)})
        raise
    record({"command": command, "params": params, "result": result})
    return result


def reference_bytes(view):
    directory = Path(os.environ["EXPERIMENT_REFERENCE_DIR"])
    manifest = json.loads((directory / "public.json").read_text())
    # Only explicitly declared public basenames; never turn an arbitrary view into a path.
    if view not in manifest["views"]:
        raise ValueError("Unknown public reference view")
    filename = manifest["views"][view]["file"]
    if Path(filename).name != filename or not filename.endswith(".png"):
        raise ValueError("Reference filename must be a PNG basename")
    path = directory / filename
    if path.is_symlink() or sha256(path) != manifest["views"][view]["sha256"]:
        raise ValueError("Public reference integrity failure")
    return path.read_bytes()


@mcp.tool()
def get_reference_image(view: str) -> Image:
    """Read one explicitly named public reference screenshot from the task prompt."""
    guard()
    data = reference_bytes(view)
    record({"reference_view": view})
    return Image(data=data, format="png")


@mcp.tool()
def inspect_view(view: str = "perspective") -> Image:
    """Inspect your current model: perspective, front, right, back, left, top.

    This is a Rhino viewport, not a calibrated reference camera or acceptance score.
    """
    guard()
    if view not in {"perspective", "front", "right", "back", "left", "top"}:
        raise ValueError("Unknown view")
    result = get_rhino_connection().send_command(
        "capture_viewport",
        {
            "viewport": view,
            "width": 1000,
            "height": 750,
            "show_grid": False,
            "show_axes": False,
            "show_cplane_axes": False,
            "zoom_to_fit": True,
        },
    )
    record({"candidate_view": view})
    return Image(data=base64.b64decode(result["image_data"]), format="png")


if __name__ == "__main__":
    mcp.run()
